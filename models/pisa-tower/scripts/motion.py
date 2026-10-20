"""The source project and exported glTF sample exactly this pure motion function."""
import math
def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3-2*t)
def gltf(v):return [v[0],v[2],-v[1]]
def pose(part,t,clip='BUILD_ASSEMBLY'):
    base=part['assembled_blender'];ex=part['explode_blender']
    if clip=='BUILD_EXPLODE':
        a=smooth((t-1)/8)
        return [base[i]+ex[i]*a for i in range(3)],[1,1,1],0.
    start,end=part['start_s'],part['end_s'];spawn=part['spawn_blender']
    if t<start:return spawn,[.0001]*3,part['yaw']
    # Scale recovery occurs at the spawn point before the main visible flight.
    k=smooth((t-start)/.18);a=smooth((t-start-.18)/(end-start-.18))
    if part.get('clearance_height_m'):
        # Cross the neighbouring cathedral above its roof, then descend inside
        # the subject's clear site. Geometry is unchanged; the same function is
        # sampled into the source Actions, glTF channels and render previews.
        u=max(0,min(1,(t-start-.18)/(end-start-.18)))
        if u<.55:
            h=smooth(u/.55);pos=[spawn[i]*(1-h)+base[i]*h for i in range(3)];pos[2]=spawn[2]+math.sin(math.pi*h)*3
            return pos,[.0001+.9999*k]*3,part['yaw']*(1-h)
        h=smooth((u-.55)/.45);pos=[base[0],base[1],spawn[2]*(1-h)+base[2]*h]
        return pos,[1,1,1],0.
    pos=[spawn[i]*(1-a)+base[i]*a for i in range(3)]
    pos[2]+=math.sin(math.pi*a)*part['arc_height_m']
    return pos,[.0001+.9999*k]*3,part['yaw']*(1-a)
