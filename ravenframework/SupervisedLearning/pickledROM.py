# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
  Created on May 8, 2018

  @author: talbpaul, wangc
  Originally from SupervisedLearning.py, split in PR #650 in July 2018
  Specific ROM implementation for pickledROM
"""
from .SupervisedLearning import SupervisedLearning
from ..utils import InputTypes, InputData

class pickledROM(SupervisedLearning):
  """
    Placeholder for ROMs that will be generated by unpickling from file.
  """
  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for
      class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, inputSpecification, InputData.ParameterInput, class to use for
        specifying input of cls.
    """
    specs = super().getInputSpecification()
    specs.description = r"""It is not uncommon for a reduced-order model (ROM) to be created and trained in one RAVEN run, then
    serialized to file (\emph{pickled}), then loaded into another RAVEN run to be used as a model.  When this is
    the case, a \xmlNode{ROM} with subtype \xmlString{pickledROM} is used to hold the place of the ROM that will
    be loaded from file.  The notation for this ROM is much less than a typical ROM; it usually only requires a name and
    its subtype.
    \\
    Note that when loading ROMs from file, RAVEN will not perform any checks on the expected inputs or outputs of
    a ROM; it is expected that a user know at least the I/O of a ROM before trying to use it as a model.
    However, RAVEN does require that pickled ROMs be trained before pickling in the first place.
    \\
    Initially, a pickledROM is not usable.  It cannot be trained or sampled; attempting to do so will raise an
    error.  An \xmlNode{IOStep} is used to load the ROM from file, at which point the ROM will have all the same
    characteristics as when it was pickled in a previous RAVEN run.
"""
    #### The following is for ARMA to reset certain variables.
    #### FIXME: we need to find a better way to handle it.
    #### For example, an optional attribute in ROM to indicate the actual type of ROM
    specs.addSub(InputData.parameterInputFactory("seed", contentType=InputTypes.IntegerType,
                                                 descr=r"""provides seed for VARMA and ARMA sampling.
                                                  Must be provided before training. If no seed is assigned,
                                                  then a random number will be used.""", default=None))
    multicycle = InputData.parameterInputFactory("Multicycle", contentType=InputTypes.StringType,
                                                 descr=r"""indicates that each sample of the ARMA should yield
                                                   multiple sequential samples. For example, if an ARMA model is trained to produce a year's worth of data,
                                                   enabling \xmlNode{Multicycle} causes it to produce several successive years of data. Multicycle sampling
                                                   is independent of ROM training, and only changes how samples of the ARMA are created.
                                                   \nb The output of a multicycle ARMA must be stored in a \xmlNode{DataSet}, as the targets will depend
                                                   on both the \xmlNode{pivotParameter} as well as the cycle, \xmlString{Cycle}. The cycle is a second
                                                   \xmlNode{Index} that all targets should depend on, with variable name \xmlString{Cycle}.""", default=None)
    multicycle.addSub(InputData.parameterInputFactory("cycles", contentType=InputTypes.IntegerType,
                                                 descr=r"""the number of cycles the ARMA should produce
                                                   each time it yields a sample.""", default='no-default'))
    growth = InputData.parameterInputFactory("growth", contentType=InputTypes.FloatType,
                                                 descr=r"""if provided then the histories produced by
                                                   the ARMA will be increased by the growth factor for successive cycles. This node can be added
                                                   multiple times with different settings for different targets.
                                                   The text of this node is the growth factor in percentage. Some examples are in
                                                   Table~\ref{tab:arma multicycle growth}, where \emph{Growth factor} is the value used in the RAVEN
                                                   input and \emph{Scaling factor} is the value by which the history will be multiplied.
                                                   \begin{table}[h!]
                                                     \centering
                                                     \begin{tabular}{r c l}
                                                       Growth factor & Scaling factor & Description \\ \hline
                                                       50 & 1.5 & growing by 50\% each cycle \\
                                                       -50 & 0.5 & shrinking by 50\% each cycle \\
                                                       150 & 2.5 & growing by 150\% each cycle \\
                                                     \end{tabular}
                                                     \caption{ARMA Growth Factor Examples}
                                                     \label{tab:arma multicycle growth}
                                                   \end{table}""", default=None)
    growth.addParam("targets", InputTypes.StringListType, required=True,
                  descr=r"""lists the targets
                    in this ARMA that this growth factor should apply to.""")
    growth.addParam('start_index', InputTypes.IntegerType)
    growth.addParam('end_index', InputTypes.IntegerType)
    growthEnumType = InputTypes.makeEnumType('growth', 'armaGrowthType', ['exponential', 'linear'])
    growth.addParam("mode", growthEnumType, required=True,
                  descr=r"""either \xmlString{linear} or
                    \xmlString{exponential}, determines the manner in which the growth factor is applied.
                    If \xmlString{linear}, then the scaling factor is $(1+y\cdot g/100)$;
                    if \xmlString{exponential}, then the scaling factor is $(1+g/100)^y$;
                    where $y$ is the cycle after the first and $g$ is the provided scaling factor.""")
    multicycle.addSub(growth)
    specs.addSub(multicycle)
    clusterEvalModeEnum = InputTypes.makeEnumType('clusterEvalModeEnum', 'clusterEvalModeType', ['clustered', 'truncated', 'full'])
    # for pickled Interpolated ROMCollection
    specs.addSub(InputData.parameterInputFactory('clusterEvalMode', contentType=clusterEvalModeEnum,
                                                 descr=r"""changes the structure of the samples for Clustered
                                                 Segmented ROMs. These are identical to the options for \xmlNode{evalMode}
                                                 node under \xmlNode{Segmented} """, default=None))
    specs.addSub(InputData.parameterInputFactory('maxCycles', contentType=InputTypes.IntegerType,
                                                 descr=r"""maximum number of cycles to run (default no limit)""", default=None))
    return specs

  def __init__(self):
    """
      A constructor that will appropriately intialize a supervised learning object
      @ In, None
      @ Out, None
    """
    super().__init__()
    self.printTag = 'pickledROM'
    self._dynamicHandling = False
    self.initOptionDict = {}
    self.features = ['PlaceHolder']
    self.target = 'PlaceHolder'

  def __confidenceLocal__(self,featureVals):
    """
      This should return an estimation of the quality of the prediction.
      @ In, featureVals, 2-D numpy array, [n_samples,n_features]
      @ Out, confidence, float, the confidence
    """
    pass

  def __resetLocal__(self):
    """
      Reset ROM. After this method the ROM should be described only by the initial parameter settings
      @ In, None
      @ Out, None
    """
    pass

  def __returnCurrentSettingLocal__(self):
    """
      Returns a dictionary with the parameters and their current values
      @ In, None
      @ Out, params, dict, dictionary of parameter names and current values
    """
    pass

  def __returnInitialParametersLocal__(self):
    """
      Returns a dictionary with the parameters and their initial values
      @ In, None
      @ Out, params, dict,  dictionary of parameter names and initial values
    """
    params = {}
    return params

  def __evaluateLocal__(self,featureVals):
    """
      Evaluates a point.
      @ In, featureVals, list, of values at which to evaluate the ROM
      @ Out, returnDict, dict, the evaluated point for each target
    """
    self.raiseAnError(RuntimeError, 'PickledROM has not been loaded from file yet!  An IO step is required to perform this action.')

  def __trainLocal__(self,featureVals,targetVals):
    """
      Trains ROM.
      @ In, featureVals, np.ndarray, feature values
      @ In, targetVals, np.ndarray, target values
    """
    self.raiseAnError(RuntimeError, 'PickledROM has not been loaded from file yet!  An IO step is required to perform this action.')