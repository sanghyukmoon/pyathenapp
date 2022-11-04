from athena_read import athdf, athinput
import xarray as xr
import numpy as np
from pathlib import Path
from matplotlib.colors import LogNorm

class LoadSim(object):
    """Class to prepare Athena++ simulation data analysis. Read input files and hdf5 outputs.

    Properties
    ----------
        basedir : str
            base directory of simulation output
        basename : str
            basename (tail) of basedir
        files : dict
            output file paths for athdf, hst, rst
        problem_id : str
            prefix for (athdf, hst, rst) output
        mesh : dict
            info about dimension, cell size, time, etc.
        nums : list of int
            athdf output numbers

    Methods
    -------
        load_athdf() :
            reads hdf5 file using athena_read and returns xarray object
    """

    def __init__(self, basedir):
        """Constructor for LoadSim class.

        Parameters
        ----------
        basedir : str
            Name of the directory where all data is stored
 
        """

        self.basedir = Path(basedir)
        self.basename = self.basedir.name
        
        # find output files by matching glob patterns
        self.files = {}
        patterns = dict(athinput='athinput.*',
                        hst='*.hst',
                        athdf='*.athdf',
                        rst='*.rst') # add additional patterns here
        for key, pattern in patterns.items():
            fmatches = self.basedir.glob(pattern)
            self.files[key] = sorted(fmatches)

        # unique athinput file? if not, issue warning
        if len(self.files['athinput']) == 0:
            print("WARNING: found no input file")
        elif len(self.files['athinput']) > 1:
            print("WARNING: found more than one input file")
        else:
            # get problem_id and mesh information from input file
            self.files['athinput'] = self.files['athinput'][0]
            self.athinput = athinput(self.files['athinput'])
            self.problem_id = self.athinput['job']['problem_id']
            self.mesh = self.athinput['mesh']

        # unique history dump? if not, issue warning
        if len(self.files['hst']) == 0:
            print("WARNING: found no history dump")
        elif len(self.files['hst']) > 1:
            print("WARNING: found more than one history dumps")
        else:
            self.files['hst'] = self.files['hst'][0]

        # find athdf output numbers
        self.nums = sorted(map(lambda p: int(p.name.strip('.athdf')[-5:]),
                              self.basedir.glob('*.{}'.format('athdf'))))

    def load_athdf(self, num=None):
        """Function to read Athena hdf5 file using athena_read
        return xarray object.

        Parameters
        ----------
        num : int
           Snapshot number, e.g., /basedir/problem_id.?????.athdf

        Returns
        -------
        dat : xarray object
        """
        
        # find athdf snapshot with the snapshot id = num
        fmatches = list(self.basedir.glob('*.{:05d}.athdf'.format(num)))
        if (len(fmatches) == 0):
            raise FileNotFoundError
        if (len(fmatches) > 1):
            raise Exception("Pattern matches more than one file")
        
        # read athdf file using athena_read
        dat = athdf(fmatches[0])
        
        # convert to xarray object
        varnames = np.array(dat['VariableNames'], dtype=str)
        variables = [(['z', 'y', 'x'], dat[varname]) for varname in varnames]
        ds = xr.Dataset(
            data_vars=dict(zip(varnames, variables)),
            coords=dict(
                x=dat['x1v'],
                y=dat['x2v'],
                z=dat['x3v']
            ),
            attrs=dict(MaxLevel=dat['MaxLevel'],
                      MeshBlockSize=dat['MeshBlockSize'],
                      NumCycles=dat['NumCycles'],
                      NumMeshBlocks=dat['NumMeshBlocks'],
                      RootGridSize=dat['RootGridSize'],
                      RootGridX1=dat['RootGridX1'],
                      RootGridX2=dat['RootGridX2'],
                      RootGridX3=dat['RootGridX3'],
                      time=dat['Time'],
                      dx=dat['x1f'][1]-dat['x1f'][0],
                      dy=dat['x2f'][1]-dat['x2f'][0],
                      dz=dat['x3f'][1]-dat['x3f'][0],
                      x1min=dat['RootGridX1'][0],
                      x1max=dat['RootGridX1'][1],
                      x2min=dat['RootGridX2'][0],
                      x2max=dat['RootGridX2'][1],
                      x3min=dat['RootGridX3'][0],
                      x3max=dat['RootGridX3'][1],
                      ),
        )
        return ds
