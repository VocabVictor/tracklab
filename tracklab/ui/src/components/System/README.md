# 系统监控组件

这是一个完整的系统监控界面，支持CPU多核心、GPU/NPU/TPU多卡以及分布式节点的监控。

## 组件列表

### 1. SystemOverview
系统总览组件，显示系统的基本性能指标和趋势。

**特性：**
- 实时CPU、内存、磁盘使用率
- 网络活动监控
- 性能趋势对比
- 系统详细信息

### 2. CPUMonitor
CPU多核心监控组件，显示每个CPU核心的详细信息。

**特性：**
- 总体CPU使用率
- 每个核心的使用率、频率、温度
- 负载平均值
- 进程和线程数量

### 3. AcceleratorMonitor
加速器监控组件，支持GPU、NPU、TPU的监控。

**特性：**
- 多种加速器类型支持
- 设备利用率和内存使用
- 温度、功耗、风扇转速
- 设备总览统计

### 4. NodeMonitor
分布式节点监控组件，支持集群环境的监控。

**特性：**
- 集群节点状态
- 资源使用情况
- 节点角色管理
- 心跳监控

## 使用方法

```typescript
import { SystemOverview, CPUMonitor, AcceleratorMonitor, NodeMonitor } from '@/components/System'

// 在 SystemPage 中使用
<SystemOverview 
  metrics={systemMetrics} 
  animationsEnabled={true}
/>

<CPUMonitor 
  overall={cpuOverall}
  cores={cpuCores}
  loadAverage={loadAverage}
  processes={processes}
  threads={threads}
  animationsEnabled={true}
/>
```

## 数据结构

参考 `@/types/index.ts` 中的：
- `SystemMetrics`
- `ClusterInfo`
- `NodeInfo`
- `AcceleratorDevice`
- `CPUCore`

## 样式系统

使用全局CSS类名：
- `.metric-card` - 基础指标卡片
- `.progress-bar` - 进度条容器
- `.progress-fill` - 进度条填充
- `.node-card` - 节点卡片
- `.accelerator-card` - 加速器卡片
- `.cpu-core-card` - CPU核心卡片

## 动画效果

- 淡入动画：`.animate-fade-in`
- 上滑动画：`.animate-slide-up`
- 缩放动画：`.animate-scale-in`
- 发光效果：`.animate-glow`

## 模拟数据

使用 `@/utils/mockData.ts` 生成测试数据：
```typescript
import { generateSystemMetrics, generateClusterInfo } from '@/utils/mockData'

const mockMetrics = generateSystemMetrics()
const mockCluster = generateClusterInfo()
```