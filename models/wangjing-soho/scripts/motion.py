"""Shared deterministic choreography, in Blender north/west/up metres."""
import math
def smooth(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)
def pose(part,t,clip='BUILD_ASSEMBLY'):
    base=part['assembled_blender']; ex=part['explode_blender']
    if clip=='BUILD_EXPLODE':
        a=smooth((t-1.5)/6.5)
        return [base[i]+ex[i]*a for i in range(3)],[1,1,1],0.
    start,end=part['start_s'],part['end_s']; spawn=part['spawn_blender']
    a=smooth((t-start)/(end-start))
    drop=85*(1-smooth((t-22)/5))
    if t<start:
        return spawn,[.0001]*3,part['yaw']
    # A short lateral settle and a strictly descending vertical flight.
    pos=[spawn[i]*(1-a)+(base[i]+(85 if i==2 else 0))*a for i in range(3)]
    if t>=end:pos=[base[0],base[1],base[2]+drop]
    return pos,[1,1,1],part['yaw']*(1-a)

def gltf(v):return [v[0],v[2],-v[1]]
