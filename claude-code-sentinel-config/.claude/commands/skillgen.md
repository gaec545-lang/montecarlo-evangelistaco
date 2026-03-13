GENERA UN SKILL NUEVO para: $ARGUMENTS

## PROTOCOLO DE CREACIÓN:

### 1. Análisis
- ¿Qué patrón resuelve este skill?
- ¿Cuántas veces se ha repetido manualmente?
- ¿Qué inputs necesita? ¿Qué outputs produce?

### 2. Construcción
Crea la estructura completa en `skills/[nombre-del-skill]/`:

```
skills/[nombre]/
├── SKILL.md           # Instrucciones detalladas + triggers
├── templates/         # Código boilerplate parametrizable
├── scripts/           # Scripts de automatización
└── tests/             # Tests del skill mismo
```

### 3. SKILL.md debe incluir:
- Frontmatter con name y description (description PUSHY para que se active)
- Cuándo usar el skill (triggers específicos)
- Cuándo NO usar el skill
- Paso a paso de ejecución
- Ejemplos de uso
- Validación del output

### 4. Testing del skill
- Ejecuta el skill 3 veces con inputs diferentes
- Verifica que el output es consistente
- Verifica que el código generado pasa linting
- Verifica que los tests generados realmente corren

### 5. Registro
- Agrega el skill al README del directorio skills/
- Documenta en CHANGELOG_AUTONOMOUS.md
