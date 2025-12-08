# Guía de Inicio - Migración de Pentaho a DBT

Guía completa para configurar y ejecutar el sistema automatizado de migración de Pentaho a DBT.

---

## 🚨 REGLA MEGA-IMPORTANTE

**¡NUNCA hacer commit directamente a las ramas `develop`, `master`, o `main`!**

El sistema tiene protección integrada para prevenir esto, pero siempre debes:
- ✅ Trabajar en ramas de características (`migrate/nombre_dimension`)
- ✅ Crear Pull/Merge Requests para revisión de código
- ❌ NUNCA hacer commit directamente a ramas protegidas

**El comando `/migrate` crea ramas de características automáticamente.**

---

## Inicio Rápido (5 Minutos)

### 1. Requisitos Previos

✅ **Ya instalados:**
- Git Bash (MINGW64)
- DBT Cloud CLI (`dbt.exe` en `tfses-dbt-snowflake-3030/`)
- Conexión a Snowflake configurada

✅ **Necesitas instalar:**
```bash
# GitLab CLI (si usas GitLab)
winget install gitlab.glab
glab auth login

# GitHub CLI (si usas GitHub)
winget install GitHub.cli
gh auth login
```

### 2. Configuración Única (PATH)

Ejecuta este script una vez para hacer disponible el comando `dbt` en todas partes:

```bash
cd 3030-pentaho-dbt
bash setup-dbt-path.sh
source ~/.bashrc
```

**Verifica que funcionó:**
```bash
dbt --version
# Debería mostrar: dbt Cloud CLI - 0.40.7
```

### 3. Ejecuta tu Primera Migración

```bash
# Prueba con dimensión pequeña (seguro, sin git)
/improve dim_date

# Migración a producción (con git push)
/migrate dim_approval_level
```

**¡Listo!** ✅

---

## Comprendiendo el Sistema

### Qué Hace

Convierte automáticamente **transformaciones de Pentaho** (.ktr, .kjb) en **modelos DBT listos para producción** en Snowflake:

```
XML Pentaho → Parsear → Analizar → Traducir → Generar → Validar → Git Push
```

### Dos Comandos

| Comando | Propósito | Operaciones Git | Cuándo Usar |
|---------|-----------|-----------------|-------------|
| `/improve` | Prueba local | ❌ No | Probar mejoras, experimentación segura |
| `/migrate` | Producción | ✅ Sí | Listo para desplegar a producción |

---

## Flujo de Migración

### Proceso Paso a Paso

**1. Parsear** (`pentaho-parser` skill)
```bash
Entrada:  pentaho-sources/dim_approval_level/*.ktr, *.kjb
Salida:   dimensions/dim_approval_level/metadata/pentaho_raw.json
```
Extrae SQL, variables, pasos, tablas del XML de Pentaho.

**2. Analizar** (`pentaho-analyzer` agent)
```bash
Entrada:  pentaho_raw.json, schema_registry.json
Salida:   pentaho_analyzed.json
```
Resuelve variables, clasifica tablas (bronze/silver/gold), evalúa complejidad.

**3. Construir Dependencias** (`dependency-graph-builder` agent)
```bash
Entrada:  pentaho_raw.json, pentaho_analyzed.json
Salida:   dependency_graph.json, dependency_graph.mmd
```
Determina orden de ejecución, detecta dependencias circulares.

**4. Traducir SQL** (`sql-translator` agent)
```bash
Entrada:  pentaho_analyzed.json, oracle-snowflake-rules
Salida:   *_translated.sql, translation_metadata.json
```
Convierte SQL de Oracle a Snowflake, preserva UDFs personalizados.

**5. Generar Modelos DBT** (`dbt-model-generator` agent)
```bash
Entrada:  translation_metadata.json, dbt-best-practices
Salida:   Modelos DBT en models/silver/, models/gold/
```
Crea modelos DBT listos para producción con documentación y tests.

**6. Validar Localmente** (`quality-validator` agent) ✨ **¡NUEVO!**
```bash
Ejecuta LOCALMENTE (sin esperar CI/CD):
  • dbt parse   (validación de sintaxis)
  • dbt compile (validación de templates)
  • dbt run     (crear modelos en Snowflake)
  • dbt test    (tests de calidad de datos)

Si hay errores: Auto-corrección y reintento (máx 2 veces)
Si pasa: Git commit + push
```

**Tiempo Total:** ~3 minutos (antes eran 10-15 min con CI/CD)

---

## Soporte de Plataformas (GitHub & GitLab)

El sistema **auto-detecta** tu plataforma Git desde la URL remota:

### GitHub
```bash
Remoto: https://github.com/org/repo.git
→ Detectado: GitHub
→ Usa: gh CLI
→ Crea: Pull Request
```

### GitLab
```bash
Remoto: https://gitlab.com/org/repo.git
→ Detectado: GitLab
→ Usa: glab CLI
→ Crea: Merge Request
```

**¡El mismo comando `/migrate` funciona para ambos!**

---

## Archivos de Configuración

### schema_registry.json

Mapea variables de Pentaho a esquemas de Snowflake:

```json
{
  "variables": {
    "EKIP_SCHEMA": {
      "snowflake_name": "EKIP",
      "type": "external",
      "layer": "bronze"
    }
  },
  "custom_functions": [
    {
      "name": "GETENNUML",
      "preserve": true,
      "deployment_required": true
    }
  ]
}
```

**Cuándo editar:**
- Agregar nueva variable de Pentaho
- Declarar UDF personalizado (para que no se traduzca)

### TABLE_COUNT.csv (Opcional)

Usado para optimización de materialización:

```csv
schema,table,row_count
EKIP,CONTRACTS,50234
EKIP,CUSTOMERS,12500
```

**Reglas:**
- `> 10M filas` → Materializado como `table`
- `< 10M filas` → Materializado como `view`

---

## Estructura de Carpetas

```
3030-pentaho-dbt/
├── CLAUDE.md                    # Contexto para Claude Code
├── README.md                    # Resumen (inglés)
├── README_ES.md                 # Resumen (español)
├── GETTING_STARTED.md          # Esta guía (inglés)
├── GETTING_STARTED_ES.md       # Esta guía (español)
├── setup-dbt-path.sh           # Script configuración PATH
│
├── config/
│   ├── schema_registry.json    # Mapeos de variables
│   └── TABLE_COUNT.csv         # Tamaños de tablas (opcional)
│
├── pentaho-sources/                    # ENTRADA: Archivos fuente Pentaho
│   └── dim_approval_level/
│       ├── d_approval_level.ktr
│       └── *.kjb
│
├── dimensions/                 # SALIDA: Metadatos por dimensión
│   └── dim_approval_level/
│       ├── metadata/
│       │   ├── pentaho_raw.json
│       │   ├── pentaho_analyzed.json
│       │   ├── dependency_graph.json
│       │   ├── translation_metadata.json
│       │   ├── dbt_generation_report.json
│       │   └── validation_report.json
│       └── sql/
│           └── *_translated.sql
│
├── tfses-dbt-snowflake-3030/  # Repositorio DBT (git)
│   ├── dbt.exe                 # Binario DBT CLI
│   ├── profiles.yml            # Conexión Snowflake
│   ├── dbt_project.yml
│   └── models/
│       ├── bronze/_sources.yml
│       ├── silver/
│       │   ├── silver_adq/
│       │   └── silver_mas/
│       └── gold/
│
└── .claude/
    ├── skills/                 # Operaciones determinísticas
    ├── agents/                 # Análisis con IA
    └── commands/               # Orquestación de flujo
```

---

## Convenciones de Nombres DBT

El sistema sigue reglas estrictas de nombres:

| Archivo Pentaho | Modelo DBT | Capa |
|-----------------|------------|------|
| `adq_ekip_contracts.ktr` | `silver/silver_adq/stg_ekip_contracts.sql` | Silver ADQ |
| `mas_contracts.kjb` | `silver/silver_mas/mas_contracts.sql` | Silver MAS |
| `d_approval_level.ktr` | `gold/d_approval_level.sql` | Gold (dimensión) |
| `f_sales.ktr` | `gold/f_sales.sql` | Gold (hecho) |

**Patrón:**
- Quitar prefijo `adq_` → Agregar prefijo `stg_`
- Mantener prefijo `mas_`
- Mantener prefijos `d_` (dimensión) y `f_` (hecho)

---

## Tareas Comunes

### Migrar una Nueva Dimensión

```bash
# 1. Colocar archivos Pentaho
mkdir pentaho-sources/dim_customer
cp /path/to/*.ktr pentaho-sources/dim_customer/

# 2. Ejecutar migración
/migrate dim_customer

# 3. Revisar reporte de validación
cat dimensions/dim_customer/metadata/validation_report.json | jq

# 4. Revisar Merge Request y fusionar
```

### Probar Mejoras Antes de Desplegar

```bash
# Hacer cambios a agents/skills
# Probar sin operaciones git
/improve dim_customer

# Comparar resultados
diff -r tfses-dbt-snowflake-3030/models tfses-dbt-snowflake-3030-ai/models

# Si es bueno, ejecutar producción
/migrate dim_customer
```

### Agregar Nuevo Mapeo de Variable

Editar `config/schema_registry.json`:

```json
{
  "variables": {
    "NUEVO_SCHEMA": {
      "snowflake_name": "NOMBRE_SCHEMA_REAL",
      "type": "external",
      "layer": "bronze"
    }
  }
}
```

Luego re-ejecutar `/migrate`.

### Declarar UDF Personalizado

Editar `config/schema_registry.json`:

```json
{
  "custom_functions": [
    {
      "name": "MI_FUNCION_PERSONALIZADA",
      "preserve": true,
      "deployment_required": true,
      "description": "UDF personalizado - no traducir"
    }
  ]
}
```

**Recuerda:** ¡Desplegar UDF a Snowflake antes de ejecutar modelos!

---

## Solución de Problemas

### "dbt: command not found"

**Causa:** PATH no configurado

**Solución:**
```bash
source ~/.bashrc
# o
bash setup-dbt-path.sh
```

### "Cannot connect to Snowflake"

**Causa:** profiles.yml mal configurado

**Solución:**
```bash
cd tfses-dbt-snowflake-3030
dbt debug  # Probar conexión
```

Verificar que `profiles.yml` tenga credenciales correctas.

### Error "Variable not found"

**Causa:** Variable de Pentaho no está en schema_registry.json

**Solución:**
Agregar a `config/schema_registry.json`:
```json
{
  "variables": {
    "TU_SCHEMA": {
      "snowflake_name": "NOMBRE_REAL",
      "type": "external",
      "layer": "bronze"
    }
  }
}
```

### "Circular dependency detected"

**Causa:** Transformaciones de Pentaho dependen entre sí en un ciclo

**Solución:**
1. Revisar `dimensions/{dimension}/metadata/dependency_graph.mmd`
2. Identificar el ciclo
3. Rediseñar lógica de transformación para romper el ciclo
4. Ver `dependency_graph.json` para puntos de ruptura sugeridos

### Migración Falla con Errores

**El sistema:**
1. Intentará auto-corrección (fuentes faltantes, etc.) - máx 2 veces
2. Si no puede corregir: Mostrará mensaje de error claro con pasos de remediación
3. Corregir manualmente
4. Re-ejecutar `/migrate {dimension}`

---

## Referencia de Comandos

### Comandos de Migración

```bash
/migrate {dimension}          # Migración completa con git push
/improve {dimension}          # Prueba local (sin git)
/migration-status             # Ver todas las dimensiones
/migration-status {dimension} # Ver dimensión específica
```

### Comandos DBT (Local)

```bash
cd tfses-dbt-snowflake-3030

# Validación
dbt parse                              # Verificar sintaxis
dbt compile                            # Resolver templates
dbt debug                              # Probar conexión Snowflake

# Ejecución
dbt run                                # Ejecutar todos los modelos
dbt run --select tag:dim_customer      # Ejecutar dimensión específica
dbt test                               # Ejecutar todos los tests
dbt test --select tag:dim_customer     # Testear dimensión específica

# Documentación
dbt docs generate                      # Generar documentación
dbt docs serve                         # Ver documentación en navegador
```

### Comandos Git (si es necesario)

```bash
cd tfses-dbt-snowflake-3030

# Ver estado
git status
git branch  # Ver rama actual
git log --oneline -10

# Crear MR/PR manualmente
glab mr create  # GitLab
gh pr create    # GitHub

# Ver MR/PR
glab mr view    # GitLab
gh pr view      # GitHub
```

### 🚨 Seguridad de Ramas

**CRÍTICO:** El sistema hace cumplir esta regla automáticamente:

```bash
# ✅ BIEN - Rama de característica
git checkout -b migrate/dim_customer

# ❌ MAL - Rama protegida (¡BLOQUEADO!)
git checkout develop  # Sistema abortará la migración
git checkout master   # Sistema abortará la migración
git checkout main     # Sistema abortará la migración
```

**Protección implementada:**
1. El comando `/migrate` crea rama de característica automáticamente
2. quality-validator verifica rama actual antes de hacer commit
3. Si está en rama protegida → Migración se aborta con error

**¡Estás seguro!** El sistema no te permitirá hacer commit a ramas protegidas.

---

## Consejos de Rendimiento

### Acelerar Migraciones

1. **Usar `/improve` para pruebas** - Sin operaciones git
2. **Migrar dimensiones pequeñas primero** - Probar el flujo
3. **Ejecutar en paralelo** (si múltiples dimensiones) - Cada una en terminal separada
4. **Pre-poblar TABLE_COUNT.csv** - Decisiones de materialización más rápidas

### Optimizar Costos de Snowflake

1. **Usar warehouse XSMALL** para desarrollo
2. **Limitar selección de modelos**: `dbt run --select tag:dimension`
3. **Usar vistas para tablas pequeñas** (< 10M filas)
4. **Configurar auto-suspend**: 60 segundos de inactividad

---

## ¿Qué Sigue?

### Después de la Primera Migración

1. ✅ Revisar el Merge Request
2. ✅ Verificar modelos en Snowflake
3. ✅ Ejecutar `dbt test` para verificar calidad de datos
4. ✅ Desplegar UDFs personalizados (si hay)
5. ✅ Fusionar a main

### Uso Continuo

- Migrar más dimensiones
- Refinar mapeos de variables en `schema_registry.json`
- Actualizar TABLE_COUNT.csv conforme crecen los datos
- Revisar y mejorar modelos generados

---

## Obtener Ayuda

### Documentación

- **Este archivo:** Guía de inicio
- **CLAUDE.md:** Contexto para agentes de Claude Code
- **README_ES.md:** Resumen del proyecto
- **docs/archive/:** Documentación técnica detallada

### Verificar Estado de Migración

```bash
/migration-status {dimension}
```

Muestra:
- Qué pasos se completaron
- Estado actual
- Ubicaciones de archivos de metadatos
- Próximos pasos

---

## Resumen

### Puntos Clave

✅ **Dos comandos:** `/improve` (prueba) y `/migrate` (producción)
✅ **Auto-detecta:** GitHub vs GitLab desde git remote
✅ **Validación rápida:** Comandos dbt locales (~30 segundos)
✅ **Auto-corrección:** Errores comunes corregidos automáticamente
✅ **No necesita CI/CD:** Valida localmente (configuración más simple)

### Línea de Tiempo Típica

```
Migración nueva dimensión: ~3 minutos
  • Parsear: 10 seg
  • Analizar: 20 seg
  • Dependencias: 10 seg
  • Traducir: 30 seg
  • Generar: 30 seg
  • Validar (dbt): 30 seg
  • Git push: 20 seg
  • Total: ~3 min
```

---

**¿Listo para comenzar?** ¡Ejecuta `/migrate dim_date` para probar con una dimensión pequeña! 🚀

---

**Versión:** 3.0 (Validación Local)
**Última Actualización:** 2025-01-27
**Complejidad:** Baja-Media
