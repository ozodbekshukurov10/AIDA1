# AIDA Distributed Event Bus

**Document:** Book 2, Chapter 4 — Distributed Event Bus
**Version:** 1.0.0
**Date:** 2026-07-04

---

## 1. Overview

The Distributed Event Bus enables event delivery across multiple nodes in a cluster. It provides replication, partitioning, leader election, and fault tolerance for horizontal scalability.

---

## 2. Cluster Architecture

### 2.1 Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUTED EVENT BUS CLUSTER                     │
│                                                                      │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      │
│  │   Node 1     │ ←──→ │   Node 2     │ ←──→ │   Node 3     │      │
│  │  (Leader)    │      │  (Follower)  │      │  (Follower)  │      │
│  │  Partition 0 │      │  Partition 1 │      │  Partition 2 │      │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘      │
│         │                     │                     │               │
│         └─────────────────────┼─────────────────────┘               │
│                               │                                     │
│                     ┌─────────┴─────────┐                          │
│                     │   Redis Cluster   │                          │
│                     │   (6 masters,     │                          │
│                     │    6 replicas)    │                          │
│                     └───────────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Node Roles

| Role | Description | Count | Responsibility |
|------|-------------|-------|----------------|
| **Leader** | Coordinates cluster | 1 | Partition assignment, rebalancing |
| **Follower** | Processes events | N-1 | Event processing, health reporting |
| **Observer** | Read-only replica | 0+ | Event storage, replay |

---

## 3. Replication

### 3.1 Replication Modes

| Mode | Consistency | Availability | Latency | Use Case |
|------|-------------|--------------|---------|----------|
| `sync` | Strong | Low | High | Critical events |
| `async` | Eventual | High | Low | Normal events |
| `quorum` | Bounded | Medium | Medium | Balanced |

### 3.2 Sync Replication

```yaml
sync_replication:
  enabled: true
  min_replicas: 2
  timeout: 100ms
  
  # Write is acknowledged only after all replicas confirm
  # Guarantees: Strong consistency
  # Trade-off: Higher latency, lower availability
```

### 3.3 Async Replication

```yaml
async_replication:
  enabled: true
  background_sync: true
  sync_interval: 100ms
  
  # Write is acknowledged immediately
  # Replicas sync in background
  # Guarantees: Eventual consistency
  # Trade-off: Lower latency, higher availability
```

### 3.4 Quorum Replication

```yaml
quorum_replication:
  enabled: true
  min_ack: 2  # Majority of 3 nodes
  timeout: 50ms
  
  # Write is acknowledged after majority confirms
  # Guarantees: Bounded consistency
  # Trade-off: Balanced latency/availability
```

---

## 4. Partitioning

### 4.1 Partition Strategy

```yaml
partitioning:
  enabled: true
  partitions: 12
  
  # Strategy
  strategy: consistent_hash  # consistent_hash | round_robin | sticky
  
  # Consistent Hash
  consistent_hash:
    virtual_nodes: 100
    hash_function: xxhash
    
  # Partition Assignment
  assignment:
    method: balanced  # balanced | round_robin
    rebalance_interval: 60s
```

### 4.2 Partition Assignment

```
Partition Assignment (3 nodes, 12 partitions):

Node 1: Partitions 0, 3, 6, 9
Node 2: Partitions 1, 4, 7, 10
Node 3: Partitions 2, 5, 8, 11

After rebalance (Node 2 joins):

Node 1: Partitions 0, 1, 6, 7
Node 2: Partitions 2, 3, 8, 9
Node 3: Partitions 4, 5, 10, 11
```

### 4.3 Partition Key

```python
def get_partition(event: Event, partition_count: int) -> int:
    """Determine partition for event."""
    
    # Use partition key if specified
    if event.metadata.get("partition_key"):
        key = event.metadata["partition_key"]
    # Otherwise use topic
    else:
        key = event.topic
    
    # Hash and modulo
    return xxhash.xxhash64(key.encode()).intdigest % partition_count
```

---

## 5. Leader Election

### 5.1 Election Protocol

```yaml
leader_election:
  protocol: raft  # raft | gossip | redis_based
  
  # Raft Configuration
  raft:
    election_timeout: 150ms
    heartbeat_interval: 50ms
    term_duration: 30s
    
  # Redis-based (simpler)
  redis_based:
    lock_key: "eventbus:leader"
    lock_ttl: 10s
    renewal_interval: 3s
```

### 5.2 Leader Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Partition Assignment | Assign partitions to nodes |
| Rebalancing | Redistribute partitions on node join/leave |
| Health Monitoring | Monitor node health |
| Failover | Trigger failover on node failure |
| Cluster Membership | Manage node join/leave |

### 5.3 Failover

```
Node Failure Detected
    │
    ├── Leader failed?
    │   ├── YES → Trigger new election
    │   │         └── New leader elected → Reassign partitions
    │   └── NO → Continue
    │
    ├── Follower failed?
    │   ├── YES → Mark node as failed
    │   │         ├── Reassign partitions from failed node
    │   │         └── Replicate to remaining nodes
    │   └── NO → Continue
    │
    └── Recovery?
        ├── Node recovers → Rejoin cluster
        ├── Sync missed events
        └── Resume normal operation
```

---

## 6. Load Distribution

### 6.1 Load Balancing

```yaml
load_balancing:
  strategy: least_loaded  # round_robin | least_loaded | consistent_hash
  
  # Health-aware routing
  health_aware:
    enabled: true
    unhealthy_threshold: 3
    healthy_threshold: 2
    
  # Weighted routing
  weighted:
    enabled: false
    weights:
      node_1: 100
      node_2: 100
      node_3: 100
```

### 6.2 Partition Rebalancing

```python
class PartitionRebalancer:
    def rebalance(self, cluster: Cluster) -> RebalancePlan:
        """Redistribute partitions across nodes."""
        
        nodes = cluster.get_healthy_nodes()
        partitions = cluster.get_all_partitions()
        
        # Calculate ideal distribution
        ideal_per_node = len(partitions) / len(nodes)
        
        # Create rebalance plan
        plan = RebalancePlan()
        
        for node in nodes:
            current_count = len(node.partitions)
            target_count = int(ideal_per_node)
            
            if current_count > target_count:
                # Move excess partitions
                excess = node.partitions[target_count:]
                for partition in excess:
                    target_node = self.find_least_loaded(nodes, exclude=[node])
                    plan.add_move(partition, node, target_node)
            elif current_count < target_count:
                # Will receive partitions
                pass
        
        return plan
```

---

## 7. Cluster Membership

### 7.1 Node States

| State | Description |
|-------|-------------|
| `joining` | Node joining cluster |
| `active` | Node fully operational |
| `suspect` | Node possibly failed |
| `failed` | Node confirmed failed |
| `leaving` | Node gracefully leaving |
| `left` | Node left cluster |

### 7.2 Membership Protocol

```yaml
membership:
  protocol: gossip  # gossip | raft | static
  
  # Gossip Configuration
  gossip:
    interval: 1s
    fanout: 3
    timeout: 10s
    
  # Static Configuration (for small clusters)
  static:
    nodes:
      - id: node_1
        host: localhost
        port: 7001
      - id: node_2
        host: localhost
        port: 7002
      - id: node_3
        host: localhost
        port: 7003
```

### 7.3 Node Join/Leave

```python
class ClusterMembership:
    async def join(self, node: Node):
        """Join cluster."""
        # Add to membership
        self.members.add(node)
        
        # Gossip membership to others
        await self.gossip_membership()
        
        # Assign partitions
        await self.rebalance_partitions()
        
    async def leave(self, node: Node):
        """Gracefully leave cluster."""
        # Mark as leaving
        node.state = "leaving"
        
        # Transfer partitions
        await self.transfer_partitions(node)
        
        # Remove from membership
        self.members.remove(node)
        
        # Gossip membership update
        await self.gossip_membership()
```

---

## 8. Data Consistency

### 8.1 Consistency Levels

| Level | Description | Guarantee |
|-------|-------------|-----------|
| `eventual` | Eventually consistent | All nodes converge |
| `bounded` | Bounded staleness | Within time/ops limit |
| `strong` | Strong consistency | Always consistent |

### 8.2 Conflict Resolution

```yaml
conflict_resolution:
  strategy: last_write_wins  # last_write_wins | vector_clock | custom
  
  # Last Write Wins
  last_write_wins:
    timestamp_based: true
    clock_skew_tolerance: 100ms
    
  # Vector Clock
  vector_clock:
    enabled: false
    max_clock_size: 100
```

---

## 9. Monitoring

### 9.1 Cluster Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Cluster size | Active nodes | Track |
| Leader node | Current leader | Track |
| Partitions per node | Distribution | Balanced |
| Replication lag | Sync delay | < 100ms |
| Consumer lag per partition | Processing delay | < 1000 |
| Node health | Health status | All healthy |

### 9.2 Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                  CLUSTER DASHBOARD                                │
│                                                                  │
│  Cluster Status: HEALTHY (3/3 nodes)                            │
│  Leader: Node 1                                                 │
│                                                                  │
│  Node Status:                                                   │
│  Node 1: [ACTIVE] partitions: 4, events/s: 150, lag: 2ms      │
│  Node 2: [ACTIVE] partitions: 4, events/s: 145, lag: 3ms      │
│  Node 3: [ACTIVE] partitions: 4, events/s: 155, lag: 1ms      │
│                                                                  │
│  Partition Distribution:                                        │
│  Node 1: [0, 3, 6, 9]                                         │
│  Node 2: [1, 4, 7, 10]                                        │
│  Node 3: [2, 5, 8, 11]                                        │
│                                                                  │
│  Replication:                                                   │
│  Mode: async                                                    │
│  Lag: avg 2ms, max 5ms                                         │
│  Throughput: 450 events/s                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Configuration

```yaml
distributed:
  enabled: true
  
  # Cluster
  cluster:
    node_id: auto
    listen_host: 0.0.0.0
    listen_port: 7000
    
  # Replication
  replication:
    mode: async
    factor: 3
    sync_interval: 100ms
    
  # Partitioning
  partitioning:
    enabled: true
    partitions: 12
    strategy: consistent_hash
    
  # Leader Election
  leader_election:
    enabled: true
    protocol: redis_based
    
  # Cluster Membership
  membership:
    protocol: gossip
    gossip_interval: 1s
    
  # Load Balancing
  load_balancing:
    strategy: least_loaded
    health_aware: true
    
  # Failover
  failover:
    enabled: true
    auto_failover: true
    failover_timeout: 10s
```
