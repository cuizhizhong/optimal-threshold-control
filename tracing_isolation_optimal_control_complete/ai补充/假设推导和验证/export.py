import numpy as np, csv
d=np.load('scan.npz'); ps,Ks=d['ps'],d['Ks']
reg,tau,M,G4b,sst,s1,G1f,G1g,arclen=d['regime'],d['tau'],d['Marc'],d['G4b'],d['sstar'],d['s1'],d['G1frac'],d['G1gap'],d['arclen']
cost,fb,nrf=d['cost'],d['fillbox'],d['nroot_fine']
P,KK=np.meshgrid(ps,Ks); h=0.15/P; ipk=0.01+0.99-h+h*np.log(h/0.99)
lab={0:'I_no_control',1:'III_boundary_then_q1',2:'II_direct_q1'}
rows=[]
for ik in range(len(Ks)):
    for ip in range(len(ps)):
        r=int(reg[ik,ip])
        rows.append(dict(p=ps[ip],K=Ks[ik],h=h[ik,ip],i_pk=ipk[ik,ip],K_over_ipk=KK[ik,ip]/ipk[ik,ip],
            regime=lab.get(r,str(r)),s1=s1[ik,ip],s_switch=sst[ik,ip],
            n_roots_D=nrf[ik,ip],tau_transversality=tau[ik,ip],M_q1_arc_margin=M[ik,ip],
            G4b_min_relD=G4b[ik,ip],G1_reachable_frac=G1f[ik,ip],G1_gap=G1g[ik,ip],
            q1_arc_rel_len=arclen[ik,ip],J_star=cost[ik,ip],J_fillbox=fb[ik,ip],
            saving_pct=100*(fb[ik,ip]-cost[ik,ip])/fb[ik,ip] if fb[ik,ip]==fb[ik,ip] else np.nan))
with open('/mnt/user-data/outputs/g3_g4_scan.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("CSV 行数:",len(rows))

# 补充统计: q=1 弧长与 K 的关系
sw=(reg==1)|(reg==2); Kf=KK/ipk
print("\nK/i_pk 分层 —— q=1 弧相对长度 与 (s*-h)/(s0-h)")
for lo,hi in [(0,.1),(.1,.3),(.3,.5),(.5,.7),(.7,.9),(.9,1.)]:
    b=sw&(Kf>=lo)&(Kf<hi)&~np.isnan(arclen)
    if b.sum()<5: continue
    print(f"  [{lo:.1f},{hi:.1f})  弧长中位={np.median(arclen[b]):.4f}  (s*-h)/(s0-h)中位={np.median((sst[b]-h[b])/(0.99-h[b])):.4f}")
