import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, ListedColormap, BoundaryNorm
plt.rcParams['font.sans-serif']=['Noto Sans CJK JP','WenQuanYi Zen Hei']
plt.rcParams['axes.unicode_minus']=False
plt.rcParams['font.size']=9

d=np.load('scan.npz'); ps,Ks=d['ps'],d['Ks']
reg,tau,M,G4b,sst,s1=d['regime'],d['tau'],d['Marc'],d['G4b'],d['sstar'],d['s1']
cost,fb,G1f=d['cost'],d['fillbox'],d['G1frac']
sv=100*(fb-cost)/fb
P,KK=np.meshgrid(ps,Ks)
h=0.15/P; ipk=0.01+0.99-h+h*np.log(h/0.99)
ext=[ps[0],ps[-1],Ks[0],Ks[-1]]
def base(ax,t):
    ax.set_xlabel('传播概率 $p$'); ax.set_ylabel('医疗容量 $K$'); ax.set_title(t)
    ax.plot(ps,0.01+0.99-0.15/ps+0.15/ps*np.log((0.15/ps)/0.99),'w-',lw=2)
    ax.plot(0.5,0.15,'w*',ms=14,mec='k',mew=.8); ax.set_xlim(ps[0],ps[-1]); ax.set_ylim(Ks[0],Ks[-1])

fig,axs=plt.subplots(2,3,figsize=(15.5,8.6))

# (a) 结构分区
ax=axs[0,0]
cm=ListedColormap(['#dfe6ec','#f2b880','#7fb3d5'])
im=ax.imshow(np.where(reg==0,0,np.where(reg==1,1,2)),origin='lower',extent=ext,
             aspect='auto',cmap=cm,norm=BoundaryNorm([-.5,.5,1.5,2.5],3))
base(ax,'(a) 最优结构分区')
cb=fig.colorbar(im,ax=ax,ticks=[0,1,2]); cb.ax.set_yticklabels(['I: $q\\equiv0$','III: $0\\!\\to\\!q_B\\!\\to\\!1\\!\\to\\!0$','II: $0\\!\\to\\!1\\!\\to\\!0$'])

# (b) G3 横截性
ax=axs[0,1]
im=ax.imshow(np.where(np.isnan(tau),np.nan,tau),origin='lower',extent=ext,aspect='auto',
             cmap='viridis',norm=LogNorm(vmin=5e-4,vmax=2.5))
c=ax.contour(P,KK,np.where(np.isnan(tau),np.nan,tau),[0.01,0.05,0.1],colors='r',linewidths=[1.6,1.1,.8])
ax.clabel(c,fmt='%g',fontsize=7)
base(ax,'(b) G3 横截性 $\\tau=s^*D\'(s^*)/|\\Theta|$\n(处处 $>0$；红线为弱横截等值线)')
fig.colorbar(im,ax=ax)

# (c) G4a
ax=axs[0,2]
im=ax.imshow(np.where(np.isnan(M),np.nan,np.maximum(M,1e-9)),origin='lower',extent=ext,
             aspect='auto',cmap='magma',norm=LogNorm(vmin=1e-8,vmax=2e-2))
c=ax.contour(P,KK,np.where(np.isnan(M),np.nan,np.maximum(M,1e-9)),[1e-4,1e-3],colors='c',linewidths=1.2)
ax.clabel(c,fmt='%.0e',fontsize=7)
base(ax,'(c) G4a  $q=1$ 弧裕度 $M$\n($M\\to0$ 表示完全跟踪段退化)')
fig.colorbar(im,ax=ax)

# (d) G4b
ax=axs[1,0]
im=ax.imshow(np.where(np.isnan(G4b),np.nan,G4b),origin='lower',extent=ext,aspect='auto',
             cmap='cividis',norm=LogNorm(vmin=2e-5,vmax=2e-1))
c=ax.contour(P,KK,np.where(np.isnan(G4b),np.nan,G4b),[1e-3],colors='r',linewidths=1.5)
ax.clabel(c,fmt='%.0e',fontsize=7)
base(ax,'(d) G4b  切换点外 $|D|/|\\Theta|$ 下界\n($\\to0$ 表示可能沿 $\\Gamma$ 滑行)')
fig.colorbar(im,ax=ax)

# (e) G1 可达性
ax=axs[1,1]
im=ax.imshow(np.where(reg==0,np.nan,G1f),origin='lower',extent=ext,aspect='auto',cmap='RdYlGn',vmin=0,vmax=1)
base(ax,'(e) G1  等待轨迹上 $q=1$ 特征线\n可达安全集的比例')
fig.colorbar(im,ax=ax)

# (f) 成本节省
ax=axs[1,2]
sw=(reg==1)|(reg==2)
im=ax.imshow(np.where(sw,np.maximum(sv,1e-3),np.nan),origin='lower',extent=ext,aspect='auto',
             cmap='plasma',norm=LogNorm(vmin=1e-2,vmax=60))
c=ax.contour(P,KK,np.where(sw,cost,np.nan),[0.01,0.1,0.5,1.5],colors='w',linewidths=.9)
ax.clabel(c,fmt='$J^*$=%g',fontsize=7)
base(ax,'(f) 相对 filling-the-box 的节省 %\n(白线为绝对成本 $J^*$ 等值线)')
fig.colorbar(im,ax=ax)

fig.suptitle('假设 G1/G3/G4 在 $p$–$K$ 平面上的横截性扫描  ($c=2,\\ \\gamma=0.3,\\ s_0=0.99,\\ i_0=0.01$)\n'
             '白色实线 $K=i_{\\rm pk}(p)$ 为控制/无控制分界，白星为报告基准点 $(0.5,0.15)$',fontsize=11)
fig.tight_layout(rect=[0,0,1,0.94])
fig.savefig('/mnt/user-data/outputs/G3_G4_scan_map.png',dpi=190)
print("fig1 ok")
