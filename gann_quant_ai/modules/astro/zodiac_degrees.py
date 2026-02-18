"""
Zodiac Degrees Module
Zodiac sign and degree calculations
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger


class ZodiacDegrees:
    """
    Zodiac degree calculations and conversions.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        self.signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer',
            'Leo', 'Virgo', 'Libra', 'Scorpio',
            'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
        self.elements = {
            'fire': ['Aries', 'Leo', 'Sagittarius'],
            'earth': ['Taurus', 'Virgo', 'Capricorn'],
            'air': ['Gemini', 'Libra', 'Aquarius'],
            'water': ['Cancer', 'Scorpio', 'Pisces']
        }
        
        self.modalities = {
            'cardinal': ['Aries', 'Cancer', 'Libra', 'Capricorn'],
            'fixed': ['Taurus', 'Leo', 'Scorpio', 'Aquarius'],
            'mutable': ['Gemini', 'Virgo', 'Sagittarius', 'Pisces']
        }
        
        logger.info("ZodiacDegrees initialized")
    
    def degree_to_sign(self, degree: float) -> Dict:
        """Convert absolute degree to zodiac sign position"""
        degree = degree % 360
        sign_num = int(degree // 30)
        sign_degree = degree % 30
        
        sign = self.signs[sign_num]
        
        return {
            'absolute_degree': round(degree, 2),
            'sign': sign,
            'sign_degree': round(sign_degree, 2),
            'sign_number': sign_num + 1,
            'element': self._get_element(sign),
            'modality': self._get_modality(sign)
        }
    
    def sign_to_degree(self, sign: str, degree_in_sign: float) -> float:
        """Convert sign and degree to absolute degree"""
        sign_num = self.signs.index(sign)
        return sign_num * 30 + degree_in_sign
    
    def _get_element(self, sign: str) -> str:
        """Get element for sign"""
        for element, signs in self.elements.items():
            if sign in signs:
                return element
        return 'unknown'
    
    def _get_modality(self, sign: str) -> str:
        """Get modality for sign"""
        for modality, signs in self.modalities.items():
            if sign in signs:
                return modality
        return 'unknown'
    
    def get_critical_degrees(self) -> Dict[str, List[int]]:
        """Get critical degrees in zodiac"""
        return {
            'aries_points': [0, 90, 180, 270],  # Cardinal points
            'fixed_cross': [45, 135, 225, 315],  # Fixed cross
            'anaretic': [29],  # End of sign
            'avatar': [15],  # Middle of sign
            'critical_cardinal': [0, 13, 26],
            'critical_fixed': [8, 9, 21, 22],
            'critical_mutable': [4, 17]
        }
    
    def is_critical_degree(self, degree: float) -> Dict:
        """Check if degree is critical"""
        sign_info = self.degree_to_sign(degree)
        sign_degree = sign_info['sign_degree']
        
        critical = self.get_critical_degrees()
        is_critical = False
        critical_type = None
        
        # Check anaretic (29 degrees)
        if 28.5 <= sign_degree <= 29.5:
            is_critical = True
            critical_type = 'anaretic'
        
        # Check avatar (15 degrees)
        if 14.5 <= sign_degree <= 15.5:
            is_critical = True
            critical_type = 'avatar'
        
        # Check cardinal points
        abs_deg = degree % 360
        if any(abs(abs_deg - cp) < 1 for cp in critical['aries_points']):
            is_critical = True
            critical_type = 'cardinal_point'
        
        return {
            **sign_info,
            'is_critical': is_critical,
            'critical_type': critical_type
        }
    
    def get_sign_boundaries(self) -> List[Dict]:
        """Get all sign boundary degrees"""
        boundaries = []
        
        for i, sign in enumerate(self.signs):
            boundaries.append({
                'sign': sign,
                'start_degree': i * 30,
                'end_degree': (i + 1) * 30 - 0.0001,
                'cusp_degree': i * 30,
                'element': self._get_element(sign),
                'modality': self._get_modality(sign)
            })
        
        return boundaries
    
    def price_to_zodiac(self, price: float, scale: float = 1.0) -> Dict:
        """Convert price to zodiac position"""
        # Scale price to 0-360 range
        degree = (price * scale) % 360
        return self.degree_to_sign(degree)
    
    def get_harmonic_degrees(self, base_degree: float, harmonic: int = 2) -> List[float]:
        """Get harmonic degrees from base"""
        harmonics = []
        interval = 360 / harmonic
        
        for i in range(harmonic):
            harm_deg = (base_degree + interval * i) % 360
            harmonics.append(round(harm_deg, 2))
        
        return harmonics
