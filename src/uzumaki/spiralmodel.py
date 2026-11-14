"""Smooth ring-phase model of the Uzumaki hair spiral.
Rings are circles of radius rho whose centres drift by rho*(dx,dy) from (cx,cy);
ring spacing grows from s0 (centre) to s1 (outside) with length scale L."""
import numpy as np

def F(rho, s0, s1, L):
    return rho/s1 + (L/s1)*np.log((s1 - (s1-s0)*np.exp(-rho/L))/s0)

def rho_ang(params, x, y):
    cx, cy, dx, dy = params[:4]
    qx, qy = x-cx, y-cy
    dd = dx*dx + dy*dy
    qd = qx*dx + qy*dy
    rho = (-qd + np.sqrt(qd*qd + (1-dd)*(qx*qx+qy*qy))) / (1-dd)
    ang = np.arctan2(qy - rho*dy, qx - rho*dx)
    return rho, ang

def phase(params, x, y):
    s0, s1, L, hand = params[4:8]
    rho, ang = rho_ang(params, x, y)
    return F(rho, s0, s1, L) + hand*ang/(2*np.pi), rho
