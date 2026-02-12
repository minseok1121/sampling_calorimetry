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
FILE_PATTERN = "*.root"

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

def process_damsa_data_single_file(file_path):
    results = {}
    ppipz_3d_data = []
    
    print(f">>> Analyzing single file (Event-by-Event): {file_path}")
    
    with uproot.open(file_path) as file:
        tree = file["DAMSA"]
        df = tree.arrays(["PDGID", "E", "z", "x", "y", "pz", "PPIPZ", "evtID"], library="pd")
        
        unique_evts = df['evtID'].unique()
        num_evts = len(unique_evts)
        
        # 1. 3D Plot용
        ed_df = df[df['PPIPZ'] > 0]
        if not ed_df.empty:
            ppipz_3d_data.append(ed_df[['x', 'y', 'z', 'PPIPZ']])

        not_neutrino = ~df['PDGID'].isin(NEUTRINO_IDS)
        pure_neutral = ~df['PDGID'].isin(EXCLUDE_IDS)

        # 2. 레이어별 루프
        for i, z_start in enumerate(ABS_START_Z + GAP_START_Z):
            is_abs = i < len(ABS_START_Z)
            l_idx = i if is_abs else i - len(ABS_START_Z) + 100
            type_str = "Absorber" if is_abs else "Gap"
            
            mask_z = (abs(df['z']/10 - z_start) < Z_TOLERANCE) & (df['pz'] > 0) & (df['PPIPZ'] == 0)

            for suffix, filter_mask in [("Entrance", not_neutrino), ("Pure", pure_neutral)]:
                key = f"{type_str}_{l_idx}_{suffix}"
                sub = df[mask_z & filter_mask].copy()
                
                if not sub.empty:
                    # [중요] 이벤트별 입자 수(n) 계산
                    counts_map = sub.groupby('evtID').size()
                    
                    # [보스 요청 사항] 원래 구조대로 리스트화하여 저장
                    # n: 이벤트당 총수, E, PDGID, x, y, z 순서
                    temp_list = []
                    for _, row in sub.iterrows():
                        n = counts_map[row['evtID']] # 해당 입자가 속한 이벤트의 총 입자 수
                        temp_list.append([
                            n, 
                            row['E'], 
                            row['PDGID'], 
                            row['x']/10, 
                            row['y']/10, 
                            row['z']
                        ])
                    
                    # 다시 데이터프레임으로 변환해서 저장 (draw_plots가 바로 읽을 수 있게)
                    results[key] = pd.DataFrame(temp_list, columns=['count', 'E', 'PDGID', 'x', 'y', 'z'])

    final_ppipz = pd.concat(ppipz_3d_data) if ppipz_3d_data else pd.DataFrame()
    return results, final_ppipz, num_evts
    # 1. 파일 하나만 오픈

# --- 실행부 ---
# 1. 파일 하나만 지정
target_file = glob.glob(FILE_PATTERN)[0] 
data_dicts, ppipz_3d, total_evts = process_damsa_data_single_file(target_file)

# 2. 기존 상세 플롯 (Scatter, 2D Hist, XY) 그대로 호출
for key, df in data_dicts.items():
    print(f">>> Drawing detailed plots for {key}...")
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

# 4. 통계 플롯 (분모를 total_evts로 사용)
stats_data = []
for i, z_pos in enumerate(ABS_START_Z + GAP_START_Z):
    is_abs = i < len(ABS_START_Z)
    l_idx = i if is_abs else i - len(ABS_START_Z) + 100
    type_str = "Absorber" if is_abs else "Gap"
    
    k_ent = f"{type_str}_{l_idx}_Entrance"
    k_pure = f"{type_str}_{l_idx}_Pure"
    
    # 해당 레이어의 전체 입자 수 / 총 이벤트 수
    avg_ent = len(data_dicts[k_ent]) / total_evts if k_ent in data_dicts else 0
    err_ent = np.sqrt(len(data_dicts[k_ent])) / total_evts if k_ent in data_dicts else 0
    
    avg_pure = len(data_dicts[k_pure]) / total_evts if k_pure in data_dicts else 0
    err_pure = np.sqrt(len(data_dicts[k_pure])) / total_evts if k_pure in data_dicts else 0
    
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