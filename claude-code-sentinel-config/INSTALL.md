# Instalación — Claude Code Config para Sentinel

## Estructura del paquete

```
tu-repo-sentinel/
├── CLAUDE.md                      ← COPIAR a la raíz de tu repo
├── CHANGELOG_AUTONOMOUS.md        ← COPIAR a la raíz
├── .claude/
│   ├── settings.json              ← Config de permisos (autonomía total)
│   └── commands/
│       ├── beast.md               ← /beast [objetivo]  → Modo construcción total
│       ├── stress.md              ← /stress [módulo]   → Stress test completo
│       ├── fix.md                 ← /fix [bug]         → Fix autónomo
│       ├── audit.md               ← /audit [módulo]    → Auditoría técnica
│       ├── skillgen.md            ← /skillgen [patrón] → Crear skill nuevo
│       └── migrate.md             ← /migrate [tabla]   → Migración Supabase
└── skills/
    └── README.md                  ← Registro de skills auto-generados
```

## Pasos de instalación

1. Copia TODO el contenido de este paquete a la raíz de tu repositorio de Sentinel
2. Verifica que `.claude/settings.json` tiene los permisos correctos
3. Abre Claude Code en el directorio del repo
4. Claude Code leerá automáticamente el CLAUDE.md

## Uso

### Modo Beast (construcción completa)
```
/beast implementar sistema de alertas proactivas por email cuando riesgo > umbral
```

### Stress Test
```
/stress módulo de Monte Carlo
```

### Fix autónomo
```
/fix la simulación da timeout cuando hay más de 5000 registros
```

### Auditoría
```
/audit todo el directorio sentinel/core/
```

### Crear skill
```
/skillgen template para componentes Streamlit con error handling
```

### Migración
```
/migrate tabla de alertas con umbrales por organización
```

## Configuración adicional recomendada

En tu archivo `~/.claude/settings.json` (global), agrega:

```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Read(*)", 
      "Write(*)",
      "Edit(*)"
    ]
  }
}
```

Esto evita que Claude Code te pregunte por permisos de lectura/escritura/ejecución en cada archivo.
