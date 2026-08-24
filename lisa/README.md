# 🔥 LISA — Autonomous Exploit Framework (V1-V20)

Lisa is the autonomous pentest engine powering the BEAST Cyber Arsenal.  
20 versions from basic recon to full WARFRAME destructive chain.

## 📁 Structure

```
lisa/
├── exec/           # 31 executable Python scripts (V1-V20 + variants)
│   ├── lisa_v8_exec.py           # V1: Recon Beast
│   ├── lisa_v8_exec_v2.py        # V2: WAF Annihilator
│   ├── lisa_v8_exec_v3.py        # V3: Origin Slayer
│   ├── lisa_v8_exec_v4.py        # V4: Shadow Protocol
│   ├── lisa_v8_exec_v5.py        # V5: Omega Protocol
│   ├── lisa_v8_exec_v6.py        # V6: Nemesis Protocol
│   ├── lisa_v8_exec_v7.py        # V7
│   ├── lisa_v8_exec_v8.py        # V8
│   ├── lisa_v8_exec_v9.py        # V9: Apex Protocol
│   ├── lisa_v8_exec_v10.py       # V10: Beast Protocol
│   ├── lisa_v8_exec_v11.py       # V11: Beast-X Protocol
│   ├── lisa_v8_exec_v12.py       # V12
│   ├── lisa_v8_exec_v14.py       # V14
│   ├── lisa_v8_exec_v15.py       # V15
│   ├── lisa_v8_exec_v16.py       # V16
│   ├── lisa_v8_exec_v17.py       # V17
│   ├── lisa_v8_exec_v18.py       # V18
│   ├── lisa_v8_exec_v19.py       # V19
│   ├── lisa_v8_exec_v20.py       # V20: WARFRAME (destructive chain)
│   ├── lisa_v4_joomla.py         # Joomla-specific
│   ├── lisa_v5.py / _probe.py    # V5 standalone
│   ├── lisa_v6.py / lisa_v7.py   # V6/V7 standalone
│   ├── lisa_v8.py / lisa_v9.py   # V8/V9 standalone
│   ├── lisa_v13_yzu_turnitin.py  # YZU Turnitin exploit
│   ├── lisa_head2head.py         # Benchmark
│   ├── lisa-v4-vs-v3-head2head.py
│   └── lisa_glm_test.py          # GLM model test
│
└── jailbreaks/     # 11 Lisa jailbreak personas (.md)
    ├── lisa-v3-null-void.md
    ├── lisa-v3-academic-override.md
    ├── lisa-v4-omega-protocol.md
    ├── lisa-v5-gacor.md
    ├── lisa-v6-absolute.md
    ├── lisa-v7-warlord.md
    ├── lisa-v8-singularity.md
    ├── lisa-v9-quantum.md
    ├── lisa-v12-fraud.md
    ├── lisa-glm-edition.md
    └── lisa-all-jailbreaks.md
```

## 🚀 Usage

### Via Cyber Arsenal MCP
```python
# List all Lisa modules
mcp_cyber_arsenal_list_lisa_modules()

# Run specific version
mcp_cyber_arsenal_run_lisa(target="https://target.com", version="v10", focus="wp")
```

### Direct execution
```bash
python3 lisa/exec/lisa_v8_exec_v20.py https://target.com --focus rce
python3 lisa/exec/lisa_v8_exec.py https://target.com --fast
```

## 📊 Version Map

| Version | Name | Script | Focus |
|---------|------|--------|-------|
| V1 | Recon Beast | lisa_v8_exec.py | whatweb + CVE + AI |
| V2 | WAF Annihilator | lisa_v8_exec_v2.py | 5 upload vectors + smuggling |
| V3 | Origin Slayer | lisa_v8_exec_v3.py | IP discovery + BigIP bypass |
| V4 | Shadow Protocol | lisa_v8_exec_v4.py | User spray + session hijack |
| V5 | Omega Protocol | lisa_v8_exec_v5.py | Adaptive jailbreak + async |
| V6 | Nemesis Protocol | lisa_v8_exec_v6.py | Browser + captcha bypass |
| V9 | Apex Protocol | lisa_v8_exec_v9.py | AI Orchestrator + Auto-Fuzz |
| V10 | Beast Protocol | lisa_v8_exec_v10.py | curl_cffi CF killer + WP |
| V11 | Beast-X | lisa_v8_exec_v11.py | ProxyRotator + CI3 + Batch |
| V20 | WARFRAME | lisa_v8_exec_v20.py | Webshell → RCE → Post → Exfil |

## 🔗 Integration

- **Cyber Arsenal MCP**: `~/.hermes/cyber-arsenal-mcp.py` → `LISA_DIR` points here
- **BEAST Terminal**: `/load lisa-v6-absolute` activates persona
- **Skills API**: 6 Lisa skills under `pentest/` category