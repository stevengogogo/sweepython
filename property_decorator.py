# -*- coding: utf-8 -*-
"""
Created on Thu Jun 02 16:45:58 2016

@author: sweel_Rafelski
"""

import math

class Vector(object):
    """
    This examples shows how to have a private attribute (_angle_deg) with a
    public interface expectign the angle in radians (rad_input_value).
    The public attr to the objects angle is Vector.rad() and Vector.deg()
    for the angles in radians and degrees.
    """
    def __init__(self, rad_input_value):
       self.rad = rad_input_value  # calls angle.setter

    @property
    def rad(self):
#        # getting rad attri in radians automatically sets
#        # the private angle deg attr
#        return math.radians(self._angle_deg)  # sets the _angle_deg attr
        return math.radians(self._angle_deg)

    @rad.setter
    def rad(self, angle_rad):
#        pass
         # this sets the private attr _angle_deg
        self._angle_deg = math.degrees(angle_rad)


    # Public interface for object angle in degrees attribute
    @property
    def deg(self):
        return self._angle_deg
#
    @deg.setter
    def deg(self, degree):
        self._angle_deg = degree

#    angle_deg = property(get_angle_deg, set_angle_deg)
#v = Vector(2*math.pi)
#print v.rad
#v.deg = 310
#print "{} radians,  {} degrees".format(v.rad, v.deg)
#v.rad = 1.01
#print "{} radians,  {} degrees".format(v.rad, v.deg)


class Vector2(object):
    """
    this example will initialize the expected input (radinput, in radians)
    as private _angle_deg attribute, in degrees. The constructor will call the
    angle setter to initialize _angle_deg
    """
    def __init__(self, radinput):
        self._angle_deg = math.degrees(radinput)

    @property
    def angle(self):
        return math.radians(self._angle_deg)

    @angle.setter
    def angle(self, value):
        self._angle_deg = math.degrees(value)

foo = Vector2(0.5*math.pi)
print foo.angle  # old angle attr will output radians as before
print foo._angle_deg  # but new private attribute is in degrees

