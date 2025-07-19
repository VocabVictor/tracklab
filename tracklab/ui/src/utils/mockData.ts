import { SystemMetrics, ClusterInfo, NodeInfo, AcceleratorDevice, CPUCore } from '@/types'

// 生成随机数据的工具函数
const randomBetween = (min: number, max: number): number => {
  return Math.random() * (max - min) + min
}

const randomInt = (min: number, max: number): number => {
  return Math.floor(randomBetween(min, max))
}

// 生成 CPU 核心数据
export const generateCPUCores = (count: number = 8): CPUCore[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    usage: randomBetween(10, 85),
    frequency: randomBetween(1800, 4200),
    temperature: randomBetween(35, 75)
  }))
}

// 生成加速器设备数据
export const generateAcceleratorDevices = (count: number = 2): AcceleratorDevice[] => {
  const types = ['gpu', 'npu', 'tpu'] as const
  const names = [
    'NVIDIA GeForce RTX 4090',
    'NVIDIA Tesla V100',
    'AMD Radeon RX 7900 XTX',
    'Intel Arc A770',
    'Google TPU v4',
    'Huawei Ascend 910'
  ]
  
  return Array.from({ length: count }, (_, i) => {
    const type = types[i % types.length]
    const totalMemory = randomBetween(8, 24) * 1024 * 1024 * 1024 // GB to bytes
    const usedMemory = totalMemory * randomBetween(0.1, 0.8)
    
    return {
      id: i,
      type,
      name: names[i % names.length],
      utilization: randomBetween(20, 95),
      memory: {
        used: usedMemory,
        total: totalMemory,
        percentage: (usedMemory / totalMemory) * 100
      },
      temperature: randomBetween(45, 85),
      power: randomBetween(150, 350),
      fanSpeed: randomBetween(30, 80)
    }
  })
}

// 生成系统指标数据
export const generateSystemMetrics = (nodeId: string = 'local'): SystemMetrics => {
  const cores = generateCPUCores()
  const accelerators = generateAcceleratorDevices()
  
  const totalMemory = 32 * 1024 * 1024 * 1024 // 32GB
  const usedMemory = totalMemory * randomBetween(0.3, 0.8)
  
  const totalDisk = 1024 * 1024 * 1024 * 1024 // 1TB
  const usedDisk = totalDisk * randomBetween(0.2, 0.7)
  
  const totalSwap = 16 * 1024 * 1024 * 1024 // 16GB
  const usedSwap = totalSwap * randomBetween(0.0, 0.3)
  
  return {
    nodeId,
    timestamp: Date.now(),
    cpu: {
      overall: cores.reduce((sum, core) => sum + core.usage, 0) / cores.length,
      cores,
      loadAverage: [
        randomBetween(0.5, 3.0),
        randomBetween(0.8, 2.5),
        randomBetween(1.0, 2.0)
      ],
      processes: randomInt(150, 400),
      threads: randomInt(800, 2000)
    },
    memory: {
      usage: (usedMemory / totalMemory) * 100,
      used: usedMemory,
      total: totalMemory,
      swap: {
        used: usedSwap,
        total: totalSwap,
        percentage: (usedSwap / totalSwap) * 100
      }
    },
    disk: {
      usage: (usedDisk / totalDisk) * 100,
      used: usedDisk,
      total: totalDisk,
      ioRead: randomBetween(10, 100) * 1024 * 1024, // MB/s
      ioWrite: randomBetween(5, 50) * 1024 * 1024, // MB/s
      iops: randomInt(1000, 10000)
    },
    network: {
      bytesIn: randomBetween(1, 10) * 1024 * 1024, // MB/s
      bytesOut: randomBetween(0.5, 5) * 1024 * 1024, // MB/s
      packetsIn: randomInt(1000, 10000),
      packetsOut: randomInt(500, 5000),
      connections: randomInt(50, 200)
    },
    accelerators
  }
}

// 生成节点信息
export const generateNodeInfo = (count: number = 4): NodeInfo[] => {
  const statuses = ['online', 'offline', 'degraded'] as const
  const roles = ['master', 'worker', 'standalone'] as const
  
  return Array.from({ length: count }, (_, i) => ({
    id: `node-${i + 1}`,
    name: `Node ${i + 1}`,
    hostname: `node${i + 1}.cluster.local`,
    ip: `192.168.1.${10 + i}`,
    role: i === 0 ? 'master' : roles[randomInt(1, roles.length)],
    status: i < count - 1 ? 'online' : statuses[randomInt(0, statuses.length)],
    lastHeartbeat: Date.now() - randomInt(1000, 30000)
  }))
}

// 生成集群信息
export const generateClusterInfo = (): ClusterInfo => {
  const nodes = generateNodeInfo()
  const onlineNodes = nodes.filter(node => node.status === 'online')
  
  return {
    nodes,
    totalResources: {
      cpu: nodes.length * 16, // 16 cores per node
      memory: nodes.length * 32 * 1024 * 1024 * 1024, // 32GB per node
      accelerators: nodes.length * 2 // 2 accelerators per node
    },
    usedResources: {
      cpu: onlineNodes.length * randomBetween(4, 12),
      memory: onlineNodes.length * randomBetween(8, 24) * 1024 * 1024 * 1024,
      accelerators: onlineNodes.length * randomInt(0, 2)
    }
  }
}

// 生成历史指标数据
export const generateHistoricalMetrics = (nodeId: string = 'local', hours: number = 24): SystemMetrics[] => {
  const metrics: SystemMetrics[] = []
  const now = Date.now()
  const interval = (hours * 60 * 60 * 1000) / 100 // 100 data points
  
  for (let i = 0; i < 100; i++) {
    const timestamp = now - (99 - i) * interval
    const baseMetrics = generateSystemMetrics(nodeId)
    
    metrics.push({
      ...baseMetrics,
      timestamp
    })
  }
  
  return metrics
}

// 生成集群指标数据
export const generateClusterMetrics = (nodes: NodeInfo[]): { [nodeId: string]: SystemMetrics } => {
  const metrics: { [nodeId: string]: SystemMetrics } = {}
  
  nodes.forEach(node => {
    if (node.status === 'online') {
      metrics[node.id] = generateSystemMetrics(node.id)
    }
  })
  
  return metrics
}