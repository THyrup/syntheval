# Description: Epsilon identifiability metric
# Author: Anton D. Lautrup
# Date: 23-08-2023

import numpy as np

from ..core.metric import MetricClass

from scipy.stats import entropy

from ...utils.nn_distance import _knn_distance

def _column_entropy(labels):
        value, counts = np.unique(np.round(labels), return_counts=True)
        return entropy(counts)

class EpsilonIdentifiability(MetricClass):
    """The Metric Class is an abstract class that interfaces with 
    SynthEval. When initialised the class has the following attributes:

    Attributes:
    self.real_data : DataFrame
    self.synt_data : DataFrame
    self.hout_data : DataFrame
    self.cat_cols  : list of strings
    self.num_cols  : list of strings

    self.nn_dist   : string keyword
    self.analysis_target: variable name

    """

    def name() -> str:
        """ Name/keyword to reference the metric"""
        return 'eps_risk'

    def type() -> str:
        """ Set to 'privacy' or 'utility' """
        return 'privacy'

    def evaluate(self) -> float | dict:
        """Function for computing the epsilon identifiability risk

        Adapted from:
        Yoon, J., Drumright, L. N., & van der Schaar, M. (2020). Anonymization Through Data Synthesis Using Generative Adversarial Networks (ADS-GAN). 
        IEEE Journal of Biomedical and Health Informatics, 24(8), 2378–2388. [doi:10.1109/JBHI.2020.2980262] 
        """

        if self.nn_dist == 'euclid':
            self.real_data = self.real_data[self.num_cols]
            self.synt_data = self.synt_data[self.num_cols] 

        real = np.asarray(self.real_data)

        no, x_dim = np.shape(real)
        W = [_column_entropy(real[:, i]) for i in range(x_dim)]
        W_adjust = 1/(np.array(W)+1e-16)

        # for i in range(x_dim):
        #     real_hat[:, i] = real[:, i] * 1. / W[i]
        #     fake_hat[:, i] = fake[:, i] * 1. / W[i]

        in_dists = _knn_distance(self.real_data,self.real_data,self.cat_cols,1,self.nn_dist,W_adjust)[0]
        ext_distances = _knn_distance(self.real_data,self.synt_data,self.cat_cols,1,self.nn_dist,W_adjust)[0]

        R_Diff = ext_distances - in_dists
        identifiability_value = np.sum(R_Diff < 0) / float(no)

        self.results['eps_risk'] = identifiability_value
        return self.results

    def format_output(self) -> str:
        """ Return string for formatting the output, when the
        metric is part of SynthEval. 
|                                          :                    |"""
        string = """\
| Epsilon identifiability risk             :   %.4f           |""" % (self.results['eps_risk'])
        return string

    def normalize_output(self) -> dict:
        """ To add this metric to utility or privacy scores map the main 
        result(s) to the zero one interval where zero is worst performance 
        and one is best.
        
        pass or return None if the metric should not be used in such scores.

        Return dictionary of lists 'val' and 'err' """
        val_non_lin = np.exp(-5*self.results['eps_risk'])
        return {'val': [val_non_lin], 'err': [0]}
