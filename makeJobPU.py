#!/cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-dbg/bin/python3
import ROOT, math, random, os, sys

# 1. 실행 파일의 절대 경로를 직접 지정하세요 (가장 확실함)
# ms 폴더 안에 있는 ALPGun의 절대 경로를 적어주세요.
G4_EXE_PATH = "/data6/Users/mioh/DAMSA_FULL/ms/ALPGun" 

tmpMac = """/random/setSeeds {r1} {r2} {r3} {r4} {r5} {r6} {r7} {r8} {r9} {r10} {r11}
/run/numberOfThreads 10
#/tracking/verbose 2
/detector/absorberLength {AT} mm
/detector/gapLength 10 mm
/detector/numLayers {nL}
/detector/absorberMaterial {AM}
/detector/targetLength 15 cm
/run/initialize

# 초기화 이후 GUN 위치 설정
/gun/particle gamma
/gun/position 0 0 -1 cm
/gun/momentum 0 0 1
/gun/energy 2 GeV

/analysis/setFileName {fName}
/run/beamOn 1000
"""

# .sh 대신 ALPGun을 직접 executable로 사용하도록 condorSub 수정
condorSub = """executable              = {exePath}
universe                = vanilla
getenv                  = True
RequestCpus             = 10
RequestMemory           = 15360
arguments               = $(filename)
transfer_input_files    = $(filename)
output                  = log/$(filename)_$(Process).out
error                   = log/$(filename)_$(Process).err
accounting_group        = group_cms
+JobBatchName = "{batchName}"
queue filename matching {shFiles}*.mac
"""

ATL = ['10']
nLL = ['6']
AML = ['G4_CESIUM_IODIDE']
g4Path = os.getcwd()

for AT in ATL:
    for AM in AML:
        batchPath = g4Path + '/batch_gamma_2GeV/eBeam_8_GeV_PU_1E4_EOT_10000_pulse_15_cm_target_{AM}_AT_{AT}_GT_10'.format(AM=AM, AT=AT)
        nL = nLL[ATL.index(AT)]
        os.makedirs(batchPath + '/log', exist_ok=True) # 로그 폴더 생성
        os.chdir(batchPath)
        
        for r in range(1):
            tmpName = "DAMSA_8_GeV_eBeam_1E4_EOT_{r:03d}".format(r=r)
            with open(tmpName+'.mac', 'w') as tmpC:
                seeds = [str(int(random.random()*1000000)) for _ in range(11)]
                tmpC.write(tmpMac.format(
                    r1=seeds[0], r2=seeds[1], r3=seeds[2], r4=seeds[3], r5=seeds[4], 
                    r6=seeds[5], r7=seeds[6], r8=seeds[7], r9=seeds[8], r10=seeds[9], r11=seeds[10],
                    AT=AT, nL=nL, AM=AM, fName=tmpName
                ))
        
        # condor.sub 생성
        with open("condor.sub", "w") as condorSubmit:
            condorSubmit.write(condorSub.format(
                exePath=G4_EXE_PATH, 
                shFiles='DAMSA_', 
                batchName=batchPath.split("/")[-1]
            ))
        
        os.system("condor_submit condor.sub")
        os.chdir(g4Path)