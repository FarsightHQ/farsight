## 🏗️ FAR Database Structure Explained

### 📊 **3-Table Normalized Design**

Your CSV row:
```csv
"10.177.58.43, 10.177.58.14, 10.177.58.39","10.177.58.43, 10.177.58.14, 10.177.58.39",tcp/10334
```

Becomes this in the database:

```
┌─────────────────────────────────────────┐
│          far_rules (Main Rule)          │
├─────────────────────────────────────────┤
│ id: 8                                   │
│ request_id: 10                          │
│ action: allow                           │
│ direction: null                         │
│ canonical_hash: [binary_hash]           │
└─────────────────────────────────────────┘
                    │
                    │ rule_id = 8
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐    ┌─────────────────┐
│ far_rule_       │    │ far_rule_       │
│ endpoints       │    │ services        │
├─────────────────┤    ├─────────────────┤
│ rule_id: 8      │    │ rule_id: 8      │
│ endpoint_type:  │    │ protocol: tcp   │
│   "source"      │    │ port_ranges:    │
│ network_cidr:   │    │   {[10334,10334]}│
│   10.177.58.43/32│   └─────────────────┘
├─────────────────┤
│ rule_id: 8      │
│ endpoint_type:  │
│   "source"      │
│ network_cidr:   │
│   10.177.58.14/32│
├─────────────────┤
│ rule_id: 8      │
│ endpoint_type:  │
│   "source"      │
│ network_cidr:   │
│   10.177.58.39/32│
├─────────────────┤
│ rule_id: 8      │
│ endpoint_type:  │
│   "destination" │
│ network_cidr:   │
│   10.177.58.43/32│
├─────────────────┤
│ rule_id: 8      │
│ endpoint_type:  │
│   "destination" │
│ network_cidr:   │
│   10.177.58.14/32│
├─────────────────┤
│ rule_id: 8      │
│ endpoint_type:  │
│   "destination" │
│ network_cidr:   │
│   10.177.58.39/32│
└─────────────────┘
```

### 🔗 **How They Connect:**

1. **far_rules** = Main rule metadata
   - `id` = Primary key
   - `action` = allow/deny
   - `canonical_hash` = Deduplication

2. **far_rule_endpoints** = All IPs involved
   - `rule_id` = Foreign key to far_rules
   - `endpoint_type` = "source" or "destination"
   - `network_cidr` = Individual IP addresses

3. **far_rule_services** = All protocols/ports
   - `rule_id` = Foreign key to far_rules  
   - `protocol` = tcp/udp/icmp
   - `port_ranges` = Port numbers or ranges

### 🎯 **Why This Design?**

✅ **Normalization**: No duplicate data
✅ **Flexibility**: Multiple sources, destinations, services per rule
✅ **Scalability**: Easy to query and index
✅ **Deduplication**: canonical_hash prevents duplicates

### 🔍 **Query Example:**
To reconstruct the original firewall rule, you JOIN all 3 tables:

```sql
SELECT 
  r.action,
  e_src.network_cidr as source,
  e_dst.network_cidr as destination,
  s.protocol || '/' || s.port_ranges as service
FROM far_rules r
JOIN far_rule_endpoints e_src ON r.id = e_src.rule_id AND e_src.endpoint_type = 'source'
JOIN far_rule_endpoints e_dst ON r.id = e_dst.rule_id AND e_dst.endpoint_type = 'destination'  
JOIN far_rule_services s ON r.id = s.rule_id
WHERE r.id = 8;
```

This creates a **Cartesian product**: 3 sources × 3 destinations × 1 service = 9 combinations!
