# channel_estimator.py
import numpy as np
from typing import List, Dict, Any

class ChannelEstimator:
    def __init__(self, num_leds: int = 4, num_receivers: int = 1):
        self.num_leds = num_leds
        self.num_receivers = num_receivers
        self.channel_matrix = np.zeros((num_leds, num_receivers))
        
    def estimate_channel(
        self,
        los_gains: List[float],
        distances: List[float],
        travel_times: List[float]
    ) -> Dict[str, Any]:
        """
        Estimates the channel state parameters, updates the channel matrix H.
        Future OFDM will ingest this channel matrix.
        """
        # Update channel matrix H
        for i in range(min(self.num_leds, len(los_gains))):
            self.channel_matrix[i, 0] = los_gains[i]
            
        return {
            "channel_matrix": self.channel_matrix.tolist(),
            "estimated_los_gains": los_gains,
            "estimated_delays": travel_times,
            "estimated_distances": distances
        }
        
    def get_channel_matrix(self) -> np.ndarray:
        return self.channel_matrix
