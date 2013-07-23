from math import log10
import scipy

def num_snvs(mutation_list):
    return len([ p for p, muts in mutation_list.items() if "snv" in muts ])

def num_cnas(mutation_list):
    return len([ p for p, muts in mutation_list.items() if "amp" in muts or "del" in muts ])

def mut_heat(samples2snvs, samples2cnas, min_freq):
    n = float(len(set(samples2snvs.keys()) | set(samples2cnas.keys())))
    
    genes2mutations = {}
    for sample in samples2snvs:
        for gene in samples2snvs[sample]:
            if gene not in genes2mutations:
                genes2mutations[gene] = {}
            if sample not in genes2mutations[gene]:
                genes2mutations[gene][sample] = []
            genes2mutations[gene][sample].append("snv")
    for sample in samples2cnas:
        for gene, mut_type in samples2cnas[sample].iteritems():
            if gene not in genes2mutations:
                genes2mutations[gene] = {}
            if sample not in genes2mutations[gene]:
                genes2mutations[gene][sample] = []
            genes2mutations[gene][sample].append(mut_type)
    
    print "\t- Including %s genes in %s samples at min frequency %s" % (len(genes2mutations), int(n), min_freq)
    
    return dict([(g, len( heat ) / n) for g, heat in genes2mutations.items()
                 if num_snvs(heat) > min_freq or num_cnas(heat) > 0])        

NULL = 100
def fm_heat(gene2heat, fm_threshold, cis_threshold=0.01, CIS=False):
    print "* Creating oncodrive heat map..."
    if CIS: print "\tIncluding CIS scores at threshold", cis_threshold, "..."
    heat = dict()
    src_fm, src_cis_amp, src_cis_del = 0, 0, 0
    for g, scores in gene2heat.items():
        if CIS:
            del_score = scores["del"] if scores["del"] < cis_threshold else NULL
            amp_score = scores["amp"] if scores["amp"] < cis_threshold else NULL
            fm_score  = scores["fm"] if scores["fm"] < fm_threshold else NULL
            if fm_score == NULL and amp_score == NULL and del_score == NULL: continue
            min_val = min(del_score, amp_score, fm_score)
            heat[g] = -log10( min_val )
            if min_val == scores["fm"]: src_fm += 1
            elif min_val == scores["amp"]: src_cis_amp += 1
            elif min_val == scores["del"]: src_cis_del += 1
        else:
            if scores["fm"] >= fm_threshold: continue
            heat[g] = -log10(scores["fm"])
            src_fm += 1
    print "\t- Genes using FM score:", src_fm
    print "\t- Genes using CIS AMP score:", src_cis_amp
    print "\t- Genes using CIS DEL score:", src_cis_del
 
    return heat

def mutsig_heat(gene2mutsig, threshold=1.0):
    print "* Creating MutSig heat map..."
    gene2heat = dict([(gene, -log10(score["qval"]))
                      for gene, score in gene2mutsig.items()
                      if score["qval"] < threshold])
    print "\t- Including", len(gene2heat), "genes at threshold", threshold
    return gene2heat

def music_heat(gene2music, threshold=1.0, max_heat=15):
    print "* Creating MuSiC heat map..."
    print "\t- Mapping q-values of 0 to", max_heat
    def music_heat(qvals):
        heat = scipy.median([ qvals["FDR_CT"], qvals["FDR_LRT"], qvals["FDR_FCPT"] ])
        return -log10(heat) if heat != 0 else max_heat
    gene2heat = dict([(gene, music_heat(scores)) for gene, scores in gene2music.items()
                      if scipy.median(scores.values()) < threshold])
    print "\t- Including", len(gene2heat), "genes at threshold", threshold
    return gene2heat

def expr_filter_heat(gene2heat, genes_to_preserve):
    gene2heat = dict([(g, h) for g, h in gene2heat.items() if g in genes_to_preserve])
    return gene2heat