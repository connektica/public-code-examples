import logging
from typing import Tuple, Optional

from pydantic import BaseModel, validate_call
import numpy as np
import pyvisa


logger = logging.getLogger(__name__)


class VNAConfig(BaseModel):
    timeout: int = 1000
    write_termination: str = "\n"
    read_termination: str = "\n"


class VNA:
    name = "cka.instrument.rs.vna.zna.v1"
    config: VNAConfig

    @property
    def default_channel(self) -> int:
        return 1
    
    @property
    def min_bwidth_resolution(self) -> int:
        """
        Minimum Bandwidth Resolution in Hertz
        
        returns (int) 1
        """
        return 1
    
    @property
    def max_bwidth_resolution(self) -> int:
        """
        Maximum Bandwidth Resolution in Hertz
        
        returns (int) 1e6
        """
        return 1000000
    
    @validate_call
    def __init__(self, connection_string: str, config: Optional[VNAConfig]):
        """
        Initiate connection to instrument.
        """
        logger.info("connecting to '%s'", connection_string)
        self.config = config
        
        rm = pyvisa.ResourceManager("@py")

        try:
            self.connection = rm.open_resource(connection_string)
            self.connection.timeout = config.timeout
            self.connection.write_termination = config.write_termination
            self.connection.read_termination = config.read_termination
            
            self.write("*CLS")
            
            idn = self.query("*IDN?").strip()
            self.write("FORMat:DATA ASCii") # set data format to ascii
            
            logger.info("connection established! %s", idn)
        except Exception:
            raise RuntimeError("failed to connect")
            
    def close(self):
        """
        Closes the pyvisa session to the instrument
        """
        self.connection.close()

    @validate_call
    def write(self, cmd: str):
        """
        Send a SCPI command to the instrument.
        """
        logger.debug("[write]: %s",cmd)
        
        result = self.connection.write(cmd)
        if self.get_error_status():
            raise RuntimeError(f"command failed: {cmd}")
        return result
    
    @validate_call
    def query(self, cmd: str):
        """
        Sends a Query command to the instrument.
        """
        logger.debug("[query]: %s", cmd)
        return self.connection.query(cmd)
        
    
    def get_error_status(self):
        """
        Checks if there are any errors.
        """
        if int(self.connection.query("*STB?")) != 0:
            try:
                error_msgs = self.connection.query("SYSTem:ERRor:NEXT?")
                logger.error("command failure: %s", error_msgs)
            finally:
                self.write("*CLS")
                
            return True
        return False

    def reset(self):
        """
        Resets the instrument to default values
        """
        self.write("*RST")
        
    @validate_call
    def _get_data(self, trace: str, data_format: str = "db-phase"):
        """
            Return data given by the ZNB in the asked format.
            Input:
                - trace (string): Name of the trace from which we get data
                - data_format (string): must be:
                                        'real-imag', 'db-phase', 'amp-phase'
                                        The phase is returned in rad.
            Output:
                - Following the data_format input it returns the tupples:
                    real, imag
                    db, phase
                    amp, phase
        """
        self.write('CALC:PARameter:SEL "%s"' % (trace))
        val = self.query("CALCulate:DATa? Sdata")
        
        val = np.fromstring(val, sep=',')
        real, imag = np.transpose(np.reshape(val, (-1,2)))
        
        if data_format.lower() == "real-imag":
            return real, imag
        
        elif data_format.lower() == "db-phase":
            try:
                return 20.*np.log10(abs(real + 1j*imag)), np.angle(real + 1j*imag)
            except RuntimeError:
                logger.error("division by zero error - Phase")
                return np.ones_like(real)
        
        elif data_format.lower() == "amp-phase":
            try:
                return abs(real + 1j*imag)**2, np.angle(real + 1j*imag)
            except RuntimeError:
                logger.error("division by zero error - Amplitude")
                return np.ones_like(real)
        else:
            raise ValueError("data-format must be: 'real-imag', 'db-phase', 'amp-phase'.")
        
    
    @validate_call
    def get_traces(self, traces: Tuple[str], data_format: str = "db-phase"):
        """
        Return data given by the ZNB in the asked format.
            Input:
                - traces (tuple): Name of the traces from which we get data.
                                Should be a tuple of string.
                                ('trace1', 'trace2', ...)
                                If only one trace write ('trace1',) to
                                have a tuple.
                - data_format (string): must be:
                                        'real-imag', 'db-phase', 'amp-phase'
                                        The phase is returned in rad.
            Output:
                - Following the data_format input it returns the tupples:
                    (a1, a2), (b1, b2), ...
                    where a1, a2 are the db-phase, by default, of the trace1
                    and b1, b2 of the trace2.
        """
        temp = []
        
        for trace in traces:
            temp.append(self._get_data(trace, data_format=data_format))
        
        return temp