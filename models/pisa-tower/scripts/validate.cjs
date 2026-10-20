// Validate complete final delivery binaries with the official Khronos library.
const fs=require('node:fs/promises'),path=require('node:path'),validator=require('gltf-validator');
const root=path.resolve(__dirname,'..');
async function main(){
 const files=['pisa-tower.glb','pisa-tower-assembly.glb','pisa-tower-explode.glb','../../model-assets/geo-context/pisa-1000-v1/district.glb'];let errors=0,warnings=0;
 for(const file of files){const report=await validator.validateBytes(new Uint8Array(await fs.readFile(path.resolve(root,file))),{uri:file,maxIssues:100});errors+=report.issues.numErrors;warnings+=report.issues.numWarnings;await fs.writeFile(path.join(root,'verification',path.basename(file)+'.validator.json'),JSON.stringify(report,null,2)+'\n');console.log(file,JSON.stringify(report.issues));}
 console.log(JSON.stringify({errors,warnings}));if(errors||warnings)process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1});
