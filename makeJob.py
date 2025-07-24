#!/cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-dbg/bin/python3
import ROOT, math, random, pickle, os, sys
from array import array
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

g4Path = os.getcwd()
M = int(sys.argv[1]) #MeV
batchPath = g4Path+ '/batch/{}_MeV'.format(M)

os.makedirs(batchPath, exist_ok=True)
os.chdir(batchPath)

ma = M/1000. #GeV

tmpMac = """/random/setSeeds {r1} {r2} {r3} {r4} {r5}
/run/numberOfThreads 1
/detector/detectorLength 46. cm
/run/initialize
/analysis/setFileName {fName}
/gun/particle gamma
/gun/position {Vx} {Vy} {Vz} cm
/ALPGun/pDirPhoton1 {px1} {py1} {pz1}
/ALPGun/pDirPhoton2 {px2} {py2} {pz2}
/ALPGun/EPhoton1 {pE1} GeV
/ALPGun/EPhoton2 {pE2} GeV
/run/beamOn 1
"""

tmpSh = """#!/bin/sh
source /cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-dbg/setup.sh
cd {batchPath}
{g4Path}/ALPGun {gMac}
"""

condorSub = """executable              = $(filename)
universe                = vanilla
getenv                  = True
RequestCpus		= 1
RequestMemory		= 15360
#output 		= log/$(filename)_$(Process).out
#error 			= log/$(filename)_$(Process).err
accounting_group        = group_cms
queue filename matching ALP2gg_Ma_{}_MeV_Egamma_*.sh
"""

log = {
    'EvtNum': [], 
    'Eg1': [], 'Epx1': [], 'Epy1': [], 'Epz1': [],
    'Eg2': [], 'Epx2': [], 'Epy2': [], 'Epz2': [],
    'Vx': [], 'Vy': [], 'Vz': [],
    'theta':[], 'Etot':[]
    }

def detAcc(t1,t2,Vz):
    maxXY = 3. #cm The maximum X and Y coordinates at the front surface of the detector.
    if t1.E() < 1. or t2.E() < 1.: return False
    dz = abs(Vz)
    maxTheta = abs(math.atan(maxXY/dz))
    if (abs(t1.Theta()) < maxTheta) and (abs(t2.Theta()) < maxTheta): return True
    else: return False

for r in range(1000):
    Vx = 0
    Vy = 0
    theta = random.uniform(1E-5, 1E-3)*random.choice([-1, 1])
    phi = random.uniform(0, 2 * math.pi)
    while True:
        Egamma = random.randint(2,11) #GeV
        Vz = random.randint(-30,-1)
        Ea = Egamma - ma
        p_lab = math.sqrt(Ea**2 - ma**2)
        px = p_lab * math.sin(theta) * math.cos(phi)
        py = p_lab * math.sin(theta) * math.sin(phi)
        pz = p_lab * math.cos(theta)
        mother_lab = ROOT.TLorentzVector(px, py, pz, Egamma)
        masses = array('d', [0.0, 0.0])
        decay = ROOT.TGenPhaseSpace()
        success = decay.SetDecay(mother_lab, 2, masses)
        if not success:
            raise RuntimeError("Decay setup failed")
        decay.Generate()
        photon1 = decay.GetDecay(0)
        photon2 = decay.GetDecay(1)
        if detAcc(photon1,photon2,Vz): break
    
    tmpName = "ALP2gg_Ma_{ma}_MeV_Egamma_{Egamma}_GeV_Vz_{Vz}_cm_DAMSA_{r:03d}".format(ma=M, Egamma=Egamma, Vz=Vz, r=r)
    tmpC = open(tmpName+'.mac','w')
    r1 = "%d"%(random.random()*1000000)
    r2 = "%d"%(random.random()*1000000)
    r3 = "%d"%(random.random()*1000000)
    r4 = "%d"%(random.random()*1000000)
    r5 = "%d"%(random.random()*1000000)
    tmpC.write(tmpMac.format(
        r1=r1, r2=r2, r3=r3, r4=r4, r5=r5,
        fName=tmpName, Vx=Vx, Vy=Vy, Vz=Vz,
        px1=photon1.Px(), py1=photon1.Py(), pz1=photon1.Pz(),
        px2=photon2.Px(), py2=photon2.Py(), pz2=photon2.Pz(),
        pE1=photon1.E(), pE2=photon2.E()
    ))
    tmpC.close()
    tmpS = open(tmpName+'.sh','w')
    tmpS.write(tmpSh.format(g4Path=g4Path,batchPath=batchPath,gMac=tmpName+'.mac'))
    tmpS.close()
  
    log['EvtNum'].append(r)
    log['Eg1'].append(photon1.E())
    log['Epx1'].append(photon1.Px())
    log['Epy1'].append(photon1.Py())
    log['Epz1'].append(photon1.Pz())
    log['Eg2'].append(photon2.E())
    log['Epx2'].append(photon2.Px())
    log['Epy2'].append(photon2.Py())
    log['Epz2'].append(photon2.Pz())
    log['Vx'].append(Vx)
    log['Vy'].append(Vy)
    log['Vz'].append(Vz)
    log['theta'].append(photon1.Vect().Angle(photon2.Vect()))
    log['Etot'].append(Egamma)

os.system("chmod 755 *.sh")
condorSubmit = open("condor.sub","w")
condorSubmit.write(condorSub.format(M))
condorSubmit.close()
os.system("condor_submit condor.sub")

with open("ALP2gg_Ma_{ma}_MeV.pkl".format(ma=M, Egamma=Egamma), "wb") as f:
    pickle.dump(log, f)

plt.figure(figsize=(6, 5))
plt.hist2d(log['Eg1'], log['Eg2'], bins=(np.arange(0,12,1),np.arange(0,12,1)), cmap='viridis',norm=LogNorm())
plt.xlabel('E$_{\gamma1}$ [GeV]')
plt.ylabel('E$_{\gamma2}$ [GeV]')
plt.title(
    r'ALP $\rightarrow \gamma\gamma$, m$_a$ = {} MeV'.format(M)
)
plt.gca().set_aspect('equal', adjustable='box')  
plt.grid(True)
plt.colorbar(label='Counts')
plt.tight_layout()
plt.savefig('ALP2gg_E1E2_Ma_{}_MeV.png'.format(M))

plt.clf()
plt.yscale('log')
plt.xscale('log')
plt.hist(log['theta'], bins=np.logspace(math.log10(1E-1), math.log10(1.1), num=30))
plt.title(
    r'ALP $\rightarrow \gamma\gamma$, $\theta_{{\gamma\gamma}}$, m$_a$ = {} MeV'.format(M, Egamma)
)
plt.xlabel(r'$\theta_{\gamma\gamma}$ [rad.]')
plt.ylabel('Enteries')
plt.tight_layout()
plt.savefig('ALP2gg_theta_Ma_{}_MeV.png'.format(M))

plt.clf()
plt.hist(log['Etot'], bins=np.arange(0,12,1))
plt.xlabel('E$_{tot}$ [GeV]')
plt.ylabel('Entries')
plt.title(
    r'ALP $\rightarrow \gamma\gamma$, E$_{{tot}}$, m$_a$ = {} MeV'.format(M, Egamma)
)
plt.tight_layout()
plt.savefig('ALP2gg_Etot_Ma_{}_MeV.png'.format(M))

plt.clf()
plt.hist(log['Vz'], bins=np.arange(-30,0,1))
plt.xlabel('V$_{z}$ [cm]')
plt.ylabel('Entries')
plt.title(
    r'ALP $\rightarrow \gamma\gamma$, V$_{{z}}$, m$_a$ = {} MeV'.format(M, Egamma)
)
plt.tight_layout()
plt.savefig('ALP2gg_Vz_Ma_{}_MeV.png'.format(M))

