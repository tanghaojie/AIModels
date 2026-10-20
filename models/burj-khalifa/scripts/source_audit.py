"""Inspect saved Blender source, camera coverage and export/source parity."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from motion import pose
SC=bpy.data.scenes['BURJ_KHALIFA'];bpy.context.window.scene=SC
parts=json.loads((ROOT/'parts.json').read_text())['parts']
for p in parts:bpy.data.objects[p['node_name']].animation_data_clear()
report=dict(blender=bpy.app.version_string,scene=SC.name,fps=SC.render.fps,unit_scale=SC.unit_settings.scale_length,length_unit=SC.unit_settings.length_unit,packed_images=sum(bool(im.packed_file) for im in bpy.data.images),actions=len(bpy.data.actions),asset_parts=len(parts),geographic_roots=[o.name for o in SC.objects if 'longitude_wgs84' in o],lighting=[],cameras=[],coverage=[])
assert report['geographic_roots']==['GEO_ROOT']
for o in bpy.data.collections['BK_PREVIEW_ONLY'].objects:
    if o.type=='LIGHT':report['lighting'].append(dict(name=o.name,type=o.data.type,energy=o.data.energy,location=list(o.location),rotation_euler=list(o.rotation_euler),size=o.data.size if o.data.type=='AREA' else o.data.angle))
    if o.type=='CAMERA':report['cameras'].append(dict(name=o.name,position=list(o.location),rotation=list(o.rotation_euler),lens_mm=o.data.lens,projection=o.data.type,ortho_width_m=o.data.ortho_scale))
for mode,cam,times in [('BUILD_ASSEMBLY','CAM_assembly',[0,1,3,6,9,12,18,24,25,27,29.5,32,36]),('BUILD_EXPLODE','CAM_explode',[0,3.5,7,10.5,14])]:
    SC.camera=bpy.data.objects[cam];SC.render.resolution_x=1280;SC.render.resolution_y=960;SC.render.resolution_percentage=100
    for t in times:
        for p in parts:
            o=bpy.data.objects[p['node_name']];loc,scale,yaw=pose(p,t,mode);o.location=loc;o.scale=scale;o.rotation_euler=(0,0,yaw)
        bpy.context.view_layer.update();coords=[]
        for p in parts:
            if pose(p,t,mode)[1][0]<.001:continue
            for child in bpy.data.objects[p['node_name']].children:
                if child.type!='MESH':continue
                coords.extend(world_to_camera_view(SC,SC.camera,child.matrix_world@Vector(c)) for c in child.bound_box)
        if not coords:continue
        lo=[min(c[i] for c in coords) for i in range(2)];hi=[max(c[i] for c in coords) for i in range(2)]
        report['coverage'].append(dict(clip=mode,t=t,projected_min=lo,projected_max=hi,inside=all(x>=-.001 for x in lo) and all(x<=1.001 for x in hi)))
assert all(x['inside'] for x in report['coverage']),report['coverage']
assert report['packed_images']>=6
(ROOT/'verification'/'source.json').write_text(json.dumps(report,indent=2));print('SOURCE_AUDIT_PASSED',flush=True)
