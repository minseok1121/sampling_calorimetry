#!/cvmfs/sft.cern.ch/lcg/views/LCG_106/x86_64-el9-gcc13-dbg/bin/python3

import ROOT, sys, os, math
import matplotlib.pyplot as plt
import numpy as np
import uproot
import awkward as ak
from particle import Particle
from statsmodels.stats.weightstats import DescrStatsW
import pandas as pd

base = os.getcwd()
nEvt = 10000
dL = [x for x in os.listdir('batch') if ('5_GeV' in x) and ('A_3T_G_10T' in x)]
totGap = 13
prefix = '5_GeV_3T_'

dataL = {}

for d in dL:
    os.chdir('batch/'+d)
    rfl = [x for x in os.listdir() if x.endswith(".root")]
    valid_files = []
    
    for f in rfl:
        try:
            with uproot.open(f) as file:
                obj = file.get("DAMSA")
                if isinstance(obj, uproot.behaviors.TTree.TTree) and obj.num_entries > 0:
                    valid_files.append(os.path.abspath(f))
                else:
                    print(f"[SKIP] {f}: Not a TTree or 0 entries")
        except Exception as e:
            print(f"[ERROR] {f}: {e}")
    
    # Now concatenate only if there are valid files
    if valid_files:
        merged = uproot.concatenate({f: "DAMSA" for f in valid_files})
    else:
        print("No valid DAMSA TTrees found.")
    dataL[d] = merged
    os.chdir(base)

for d in dataL.keys():
    merged = dataL[d]
    evt_ids_np = ak.to_numpy(merged['PDGID']).astype(int)
    unique_vals, counts = np.unique(evt_ids_np, return_counts=True)
    plt.errorbar(['$'+Particle.from_pdgid(int(pdg)).latex_name+'$' for pdg in unique_vals], counts, fmt='o', yerr=np.sqrt(counts), capsize=3, alpha=0.7,label=d.replace('_',' '))
plt.xlabel("PDG ID")
plt.ylabel("Number of entries")
plt.title("Particle Type Distribution (by PDG ID)")
plt.yscale('log')
plt.legend()
plt.tight_layout()
plt.savefig(prefix+"PDGID.pdf")
plt.clf()

for d in dataL.keys():
    merged = dataL[d]
    mask = np.abs(merged["PDGID"]) == 11
    x = merged["x"][mask]
    y = merged["y"][mask]
    z = merged["z"][mask]
    E = merged["E"][mask]
    R = np.sqrt(x**2 + y**2)
    z_bins = np.arange(0, 401, totGap)  # 1 mm bins
    z_indices = np.digitize(z, bins=z_bins)
    avg_Rs = []
    sig_Rs = []
    z_centers = []
    for i in range(1, len(z_bins)):
        in_bin = z_indices == i
        if np.any(in_bin):
            R_bin = R[in_bin]
            E_bin = E[in_bin]
            stats = DescrStatsW(R_bin, weights=E_bin)
            avg_Rs.append(stats.mean)
            sig_Rs.append(stats.std)
            z_centers.append((z_bins[i] + z_bins[i-1]) / 2)
    plt.errorbar(z_centers, avg_Rs, yerr=sig_Rs, fmt='o', capsize=3, alpha=0.7, label=d.replace('_',' '))
plt.xlabel("z [mm]")
plt.ylabel("⟨r⟩ [mm]")
plt.title("Energy-weighted ⟨R⟩ vs z (e⁻ / e⁺)")
plt.legend()
plt.tight_layout()
plt.savefig(prefix+"ShowerShape_11_profile.pdf")
plt.clf()

for d in dataL.keys():
    merged = dataL[d]
    mask = np.abs(merged["PDGID"]) == 11
    z = merged["z"][mask]
    plt.hist(z, np.arange(0, 401, totGap), histtype='step', label=d.replace('_',' '))
plt.xlabel("Z position of e$^{\pm}$ [mm]")
plt.ylabel("Entries")
plt.title("Z Position")
plt.legend()
plt.tight_layout()
plt.savefig(prefix+"ZPosition_11_mask.pdf")
plt.clf()

for d in dataL.keys():
    merged = dataL[d]
    mask = np.abs(merged["PDGID"]) == 11
    evt_ids = merged["evtID"][mask]
    unique_evt_ids, counts = np.unique(evt_ids, return_counts=True)
    maxN = max(counts)
    plt.hist(counts, np.arange(0, maxN+10, 1), histtype='step', label=d.replace('_',' '))
plt.xlabel("Number of e$^{\pm}$ [N]")
plt.ylabel("Entries")
plt.title("Number of  e$^{\pm}$ per event")
plt.legend()
plt.tight_layout()
plt.savefig(prefix+"nParticle_11_mask.pdf")
plt.clf()


for d in dataL.keys():
    merged = dataL[d]
    mask = np.abs(merged["PDGID"]) == 11
    evt_ids = merged["evtID"][mask]
    z_vals = merged["z"][mask]
    sort_idx = np.argsort(evt_ids)
    evt_sorted = evt_ids[sort_idx]
    z_sorted = z_vals[sort_idx]
    unique_evtIDs, start_indices = np.unique(evt_sorted, return_index=True)
    max_z = np.empty(len(unique_evtIDs))  # ✅ fix here
    for i in range(len(start_indices)):
        start = start_indices[i]
        end = start_indices[i+1] if i+1 < len(start_indices) else len(evt_sorted)
        max_z[i] = np.max(z_sorted[start:end])
    plt.hist(max_z, bins=np.arange(0, 401, 10), histtype='step', label=d.replace('_',' '))  # ✅ fix here (use max_z not undefined max_z_per_event)

plt.xlabel("Shower length [mm]")
plt.ylabel("Entries")
plt.title("Shower Length")
plt.legend()
plt.tight_layout()
plt.savefig(prefix+"ShowerLength_11_mask.pdf")
plt.clf()

for d in dataL.keys():
    merged = dataL[d]
    mask = np.abs(merged["PDGID"]) == 11
    df = pd.DataFrame({
        "evtID": merged["evtID"][mask],
        "z": merged["z"][mask],
        "E": merged["E"][mask],
    })
    z_bins = np.arange(0, 401, totGap)
    df["z_bin"] = pd.cut(df["z"], bins=z_bins, labels=(z_bins[:-1] + totGap*0.5))
    grouped = df.groupby(["evtID", "z_bin"])["E"].sum().reset_index()
    avg_E_per_z = grouped.groupby("z_bin")["E"].mean().reset_index()
    plt.plot(avg_E_per_z["z_bin"].astype(float), avg_E_per_z["E"], label=d.replace('_',' '))
plt.xlabel("z [mm]")
plt.ylabel("Average Sum. E")
plt.title("Energy Deposition: z")
plt.tight_layout()
plt.legend()
plt.savefig(prefix+"SumE_z.pdf")
plt.clf()
exit()



targetD = {}
targetD['gamma_1_GeV'] = 'batch/gamma_1_GeV_W_5T_G_5T'
targetD['gamma_2_GeV'] = 'batch/gamma_2_GeV_W_5T_G_5T'
targetD['gamma_3_GeV'] = 'batch/gamma_3_GeV_W_5T_G_5T'
targetD['gamma_4_GeV'] = 'batch/gamma_4_GeV_W_5T_G_5T'
targetD['gamma_5_GeV'] = 'batch/gamma_5_GeV_W_5T_G_5T'
#targetD['PU_1E4_EOT_20_cm_target'] = 'batch/PU_1E4_EOT_20_cm_target'
#targetD['PU_1E5_EOT_20_cm_target'] = 'batch/PU_1E5_EOT_20_cm_target'

base = os.getcwd()

histV = {}
histV['nEntries'] = []
histV['eSum'] = []
histC = {}
histC['nEntries'] = ['The number of charged particles','N','Entries','steelblue']
histC['eSum'] = ['The energy sum. of charged particles','E [MeV]','Entries','steelblue']

for k in targetD.keys():
    os.chdir(targetD[k])
    rfl = [x for x in os.listdir() if x.endswith(".root")]
    print("# of ROOT files:",len(rfl))
    if not rfl:
        raise FileNotFoundError("No .root files found in current directory")
    histV['nEntries'].append([])
    histV['eSum'].append([])
    for x in rfl:
        tmpr = ROOT.TFile(x)
        tmp_n_entries = tmpr.Get('d_1D_all_charged_Ekin')
        tmp_e_sum = tmpr.Get('d_2D_all_charged_Z_x_w_Ekin')
        histV['nEntries'][-1].append(tmp_n_entries.Integral())
        histV['eSum'][-1].append(tmp_e_sum.Integral())
    os.chdir(base)

for k in histV.keys():
    plt.clf()
    vmax = max(itertools.chain.from_iterable(histV[k]))
    vmin = min(itertools.chain.from_iterable(histV[k]))
    if vmin == 0: vmin = 1
    if k == 'eSum': vmax = 30000
    for i, s in enumerate(histV[k]):
        label = list(targetD.keys())[i].replace('_',' ')  # get label from tar
        plt.hist(s, bins=np.linspace(vmin, vmax, 100), histtype='step', linewidth=1.5, label=label, alpha=0.7)
        #plt.hist(s, np.logspace(math.log10(vmin), math.log10(vmax), num=33), histtype='step', linewidth=1.5, label=label)
    plt.title(histC[k][0])
    plt.xlabel(histC[k][1])
    plt.ylabel(histC[k][2])
    plt.legend()
    plt.tight_layout()
    #plt.xscale('log')
    plt.yscale('log')
    plt.savefig(k+".pdf")
