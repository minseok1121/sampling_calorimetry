import uproot
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import time
from particle import Particle
from matplotlib.colors import LogNorm
from mpl_toolkits.mplot3d import Axes3D


Z_TOLERANCE = 1e-4 
PATHS = [
    "batch_330_CsIFull/eBeam_8_GeV_PU_1E4_EOT_10000_pulse_15_cm_target_G4_CESIUM_IODIDE_AT_10_GT_10/*.root",
    "batch_660_CsIFull/eBeam_8_GeV_PU_1E4_EOT_10000_pulse_15_cm_target_G4_CESIUM_IODIDE_AT_10_GT_10/*.root"
]

NEUTRINO_IDS = [12, -12, 14, -14]
EXCLUDE_IDS = NEUTRINO_IDS + [2112, 22] # 뉴트리노 + 중성자(2112) + 광자(22)

# --- [설정] 새 지오메트리에 따른 두께 (cm) ---
firstAbsThick = 2.0
firstGapThick = 0.3
commonGapThick = 0.3
cuThick  = 0.1
pcbThick = 0.3
normalAbsThick = 1.0

# --- [계산] 각 레이어의 시작(Entrance) Z 위치 리스트 ---
ABS_START_Z = []
GAP_START_Z = []

currZ = 0.0

for i in range(6): # 총 6개 레이어 (0~5)
    if i == 0:
        # --- Layer 0 ---
        # 1. Absorber 시작
        ABS_START_Z.append(currZ)
        currZ += firstAbsThick
        
        # 2. Gap 시작
        GAP_START_Z.append(currZ)
        currZ += firstGapThick
        
        # 3. Cu + 4. PCB 통과 (다음 레이어 시작점으로)
        currZ += cuThick
        currZ += pcbThick
    else:
        # --- Layer 1~5 (반복 구성: Abs -> PCB -> Gap -> Cu -> PCB) ---
        # 1. Absorber 시작
        ABS_START_Z.append(currZ)
        currZ += normalAbsThick
        
        # 2. PCB 통과 (Gap 전)
        currZ += pcbThick
        
        # 3. Gap 시작
        GAP_START_Z.append(currZ)
        currZ += commonGapThick
        
        # 4. Cu + 5. PCB 통과 (다음 레이어 시작점으로)
        currZ += cuThick
        currZ += pcbThick

print(f">>> 검증: 계산된 Absorber 시작 Z: {ABS_START_Z}")
print(f">>> 검증: 계산된 Gap 시작 Z: {GAP_START_Z}")

def draw_plots(df, title_prefix, file_prefix):
    if df.empty: return
    # 1. Scatter (입자별)
    plt.figure(figsize=(10, 6))
    for pid in df['PDGID'].unique():
        try:
            name = f"${Particle.from_pdgid(int(pid)).latex_name}$"
        except:
            name = f"PID {pid}"
        sub = df[df['PDGID'] == pid]
        plt.scatter(sub['count'] + np.random.uniform(-0.15, 0.15, len(sub)), sub['E'], label=name, s=20, alpha=0.4)
    plt.yscale('log'); plt.title(f"{title_prefix} - Scatter"); plt.legend(loc='upper right'); plt.tight_layout()
    plt.savefig(f"{file_prefix}_scatter.png"); plt.close()

    # 2. 2D Histogram (E Density)
    plt.figure(figsize=(10, 7))
    x_bins = np.arange(df['count'].min() - 0.5, df['count'].max() + 1.5, 1)
    # Y축(E) 범위 설정 (에러 방지 핵심)
    e_min, e_max = df['E'].min(), df['E'].max()
    if e_min <= 0: e_min = 0.1  # 로그 스케일을 위해 0 이하 값 방지
    
    # 만약 e_min과 e_max가 같으면 로그 스케일 빈을 만들 수 없으므로 강제로 범위를 넓힘
    if e_min == e_max:
        y_bins = np.logspace(np.log10(e_min * 0.9), np.log10(e_max * 1.1), 70)
    else:
        y_bins = np.logspace(np.log10(e_min), np.log10(e_max), 70)

    try:
        # 데이터가 너무 적거나 한 곳에 몰려있으면 LogNorm에서 에러날 수 있음
        h = plt.hist2d(df['count'], df['E'], bins=[x_bins, y_bins], 
                       norm=LogNorm() if len(df) > 1 else None, cmap='magma')
        plt.colorbar(label='Intensity')
    except:
        # 최후의 수단: LogNorm 없이 그리기
        plt.hist2d(df['count'], df['E'], bins=[x_bins, y_bins], cmap='magma')
        plt.colorbar(label='Intensity (Linear)')

    plt.yscale('log'); plt.title(f"{title_prefix} - 2D E Hist")
    plt.savefig(f"{file_prefix}_2d_hist.png"); plt.close()

    # 3. XY Profile
    plt.figure(figsize=(8, 7))
    plt.hist2d(df['x'], df['y'], bins=100, norm=LogNorm(), cmap='inferno')
    plt.colorbar(label='Intensity'); plt.axis('equal'); plt.title(f"{title_prefix} - XY Profile")
    plt.savefig(f"{file_prefix}_xy.png"); plt.close()

def process_damsa_data(limit=1000):
    # 1. 두 경로에서 파일 리스트 합치기
    file_list = []
    for p in PATHS:
        file_list.extend(glob.glob(p))
    file_list = file_list[:limit]
    
    # [Consistency Check용 변수] 경로별 총 에너지 합산용
    path_stats = {p: {"E_sum": 0, "n_particles": 0} for p in PATHS}
    
    results = {}
    ppipz_3d_data = []

    print(f">>> {len(file_list)}개 파일 분석 중... (Target: Multiple Paths)")
    
    for f_path in file_list:
        origin_path = next((p for p in PATHS if p.split('/')[0] in f_path), PATHS[0])

        try:
            with uproot.open(f_path) as file:
                tree = file["DAMSA"]
                # PPIPZ 컬럼을 에너지 디파짓으로 명시적 로드
                df = tree.arrays(["PDGID", "E", "z", "x", "y", "pz", "PPIPZ", "Charge"], library="pd")

                # --- [Consistency 데이터 누적] ---
                path_stats[origin_path]["E_sum"] += df["E"].sum()
                path_stats[origin_path]["n_particles"] += len(df)
                # ------------------------------
                
                # 1. 3D Plot용 PPIPZ 데이터 (edep > 0)
                ed_df = df[df['PPIPZ'] > 0]
                if not ed_df.empty:
                    ppipz_3d_data.append(ed_df[['x', 'y', 'z', 'PPIPZ']])

                # [필터 생성] 뉴트리노 제외 마스크
                not_neutrino = ~df['PDGID'].isin(NEUTRINO_IDS)
                pure_neutral = ~df['PDGID'].isin(EXCLUDE_IDS) # 중성자, 광자 추가 제외

                # 레이어별 데이터 수집
                for i, z_start in enumerate(ABS_START_Z):
                    # 기존 그룹 (뉴트리노만 제외)
                    key = f"Absorber_{i}_Entrance"
                    mask = (abs(df['z']/10 - z_start) < Z_TOLERANCE) & (df['pz'] > 0) & not_neutrino & (df['PPIPZ'] == 0)
                    # [신규] Pure 그룹 (중성자, 광자까지 제외)
                    key_pure = f"Absorber_{i}_Pure"
                    mask_pure = (abs(df['z']/10 - z_start) < Z_TOLERANCE) & (df['pz'] > 0) & pure_neutral & (df['PPIPZ'] == 0)
                    
                    for k, m in [(key, mask), (key_pure, mask_pure)]:
                        sub = df[m]
                        if not sub.empty:
                            n = len(sub)
                            for _, row in sub.iterrows():
                                results.setdefault(k, []).append([n, row['E'], row['PDGID'], row['x']/10, row['y']/10, row['z']])

                # Gap 부분도 동일하게 적용 (생략 가능하나 일관성을 위해 추가)
                for i, z_start in enumerate(GAP_START_Z):
                    key = f"Gap_{i+100}_Entrance"
                    mask = (abs(df['z']/10 - z_start) < Z_TOLERANCE) & (df['pz'] > 0) & not_neutrino & (df['PPIPZ'] == 0)
                    key_pure = f"Gap_{i+100}_Pure"
                    mask_pure = (abs(df['z']/10 - z_start) < Z_TOLERANCE) & (df['pz'] > 0) & pure_neutral & (df['PPIPZ'] == 0)
                    
                    for k, m in [(key, mask), (key_pure, mask_pure)]:
                        sub = df[m]
                        if not sub.empty:
                            n = len(sub)
                            for _, row in sub.iterrows():
                                results.setdefault(k, []).append([n, row['E'], row['PDGID'], row['x']/10, row['y']/10, row['z']])

        except Exception as e: print(f"Error {f_path}: {e}")

    # --- [검증 출력] ---
    print("\n" + "="*60)
    print(f"{'Path (Origin)':<30} | {'Avg E per Part':<15} | {'Total Count'}")
    print("-"*60)
    for p, stat in path_stats.items():
        avg_e = stat["E_sum"] / stat["n_particles"] if stat["n_particles"] > 0 else 0
        p_name = p.split('/')[0] # 경로의 최상위 폴더명만 출력
        print(f"{p_name:<30} | {avg_e:<15.6f} | {stat['n_particles']}")
    print("="*60 + "\n")

    final_dfs = {k: pd.DataFrame(v, columns=['count', 'E', 'PDGID', 'x', 'y', 'z']) for k, v in results.items()}
    final_ppipz = pd.concat(ppipz_3d_data) if ppipz_3d_data else pd.DataFrame()
    return final_dfs, final_ppipz

# --- 실행부 ---
data_dicts, ppipz_3d = process_damsa_data(1000)

# 1. 레이어별 3종 플롯 생성
for key, df in data_dicts.items():
    print(f">>> Drawing plots for {key}...")
    draw_plots(df, key, f"plot_{key}")

# 2. PPIPZ (Energy Deposit) 3D Plot
# 2. PPIPZ (Energy Deposit) 3D Plot & 구간별(Volume) 2D Energy Maps
if not ppipz_3d.empty:
    print(">>> Generating 3D & Layer-Volume 2D PPIPZ Energy Plots...")
    
    # [기존 3D Plot 그대로 유지]
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    sc = ax.scatter(ppipz_3d['z'], ppipz_3d['x'], ppipz_3d['y'], c=ppipz_3d['PPIPZ'], 
                    s=ppipz_3d['PPIPZ']*10, cmap='viridis', norm=LogNorm(), alpha=0.5)
    plt.colorbar(sc, label='PPIPZ (Energy Deposit [MeV])')
    ax.set_xlabel('Z (cm)'); ax.set_ylabel('X (cm)'); ax.set_zlabel('Y (cm)')
    plt.savefig("plot_3D_PPIPZ_Global.png"); plt.close()

    # [신규] 연속된 Z 리스트를 활용한 구간별(Volume) 2D Map
    # 모든 경계 지점을 합치고 중복 제거 후 정렬
    z_boundaries = sorted(list(set(np.concatenate([ABS_START_Z, GAP_START_Z]))))

    for i in range(len(z_boundaries) - 1):
        z_min, z_max = z_boundaries[i], z_boundaries[i+1]
        
        # 해당 구간(Z-Volume) 내의 데이터 필터링 (mm -> cm 변환 고려)
        layer_mask = (ppipz_3d['z']/10.0 >= z_min) & (ppipz_3d['z']/10.0 < z_max)
        layer_df = ppipz_3d[layer_mask]
        
        if layer_df.empty: continue
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        title = f"Volume_Z_{z_min:.2f}_to_{z_max:.2f}"
        
        # 1. XY Energy Map (해당 구간 내 모든 에너지 투영)
        h1 = ax1.hist2d(layer_df['x'], layer_df['y'], bins=100, weights=layer_df['PPIPZ'], 
                        norm=LogNorm(), cmap='inferno')
        plt.colorbar(h1[3], ax=ax1, label='Total PPIPZ [MeV]')
        ax1.set_title(f"XY Energy: {title}"); ax1.set_xlabel("X (cm)"); ax1.set_ylabel("Y (cm)"); ax1.axis('equal')

        # 2. YZ Energy Map (구간 내 Z축 분포 확인)
        h2 = ax2.hist2d(layer_df['z']/10.0, layer_df['y'], bins=100, weights=layer_df['PPIPZ'], 
                        norm=LogNorm(), cmap='viridis')
        plt.colorbar(h2[3], ax=ax2, label='Total PPIPZ [MeV]')
        ax2.set_title(f"YZ Energy: {title}"); ax2.set_xlabel("Z (cm)"); ax2.set_ylabel("Y (cm)")

        plt.tight_layout()
        plt.savefig(f"plot_Volume_Energy_{i:02d}.png"); plt.close()

# 3. 전체 레이어(Absorber & Gap) 입사 입자 통계
print(">>> Generating All-Layer Particle Statistics Plot...")

# 100개 파일 분석 기준 (limit과 동일하게)
num_files = 995 

stats_data = []
for key in data_dicts.keys():
    if 'Entrance' not in key: continue
    
    parts = key.split('_')
    idx = int(parts[1])
    # Z 좌표 및 타입 판별
    is_abs = 'Absorber' in key
    z_pos = ABS_START_Z[idx] if is_abs else GAP_START_Z[idx-100]
    
    key_pure = key.replace('Entrance', 'Pure')
    
    # 평균 및 Poisson Error (sqrt(N)/Total_Files)
    avg_ent = len(data_dicts[key]) / num_files if key in data_dicts else 0
    err_ent = np.sqrt(len(data_dicts[key])) / num_files if key in data_dicts else 0
    
    avg_pure = len(data_dicts[key_pure]) / num_files if key_pure in data_dicts else 0
    err_pure = np.sqrt(len(data_dicts[key_pure])) / num_files if key_pure in data_dicts else 0
    
    stats_data.append([z_pos, avg_ent, err_ent, avg_pure, err_pure, is_abs])

stats_df = pd.DataFrame(stats_data, columns=['Z', 'Ent_Mean', 'Ent_Err', 'Pure_Mean', 'Pure_Err', 'is_abs']).sort_values('Z')

# --- 시각화 (1x2 Canvas) ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7))

# [Panel 1: 전체 레이어 통계]
ax1.errorbar(stats_df['Z'], stats_df['Ent_Mean'], yerr=stats_df['Ent_Err'], fmt='o-', 
             color='tab:blue', label='All (Abs+Gap)', capsize=3, markersize=5)
ax1.errorbar(stats_df['Z'], stats_df['Pure_Mean'], yerr=stats_df['Pure_Err'], fmt='s--', 
             color='tab:red', label='Pure (Abs+Gap)', capsize=3, markersize=5)
ax1.set_yscale('log')
ax1.set_title("Full Propagation Multiplicity", fontsize=14)
ax1.set_xlabel("Z Position [cm]"); ax1.set_ylabel("Mean Multiplicity")
ax1.grid(True, which="both", ls="--", alpha=0.4); ax1.legend()

# [Panel 2: Gap 구간 Charged Particle (Pure) 전용]
gap_only = stats_df[stats_df['is_abs'] == False]
ax2.errorbar(gap_only['Z'], gap_only['Pure_Mean'], yerr=gap_only['Pure_Err'], fmt='D-', 
             color='darkorange', label='Gap Charged (Pure)', capsize=5, elinewidth=2, markersize=8)

# Gap 구간은 값 차이가 크지 않을 수 있으므로 Linear 혹은 필요시 Log 유지
# ax2.set_yscale('log') # 필요하면 주석 해제
ax2.set_title("Gap Layers: Charged Particle Statistics", fontsize=14)
ax2.set_xlabel("Z Position [cm]"); ax2.set_ylabel("Mean Multiplicity")
ax2.grid(True, ls="--", alpha=0.4); ax2.legend()

plt.tight_layout()
plt.savefig("plot_Combined_Layer_Statistics.png")
plt.close()

print(">>> 통합 캔버스 플롯 저장 완료.")