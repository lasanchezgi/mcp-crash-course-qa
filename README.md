# MCP Crash Course

Proyecto de aprendizaje para entender y construir servidores **MCP (Model Context Protocol)** usando Python.

---

## ¿Qué es MCP?

**Model Context Protocol** es un protocolo abierto desarrollado por Anthropic que estandariza la forma en que los modelos de lenguaje (LLMs) se conectan con herramientas, datos y contexto externo.

Antes de MCP cada integración era ad-hoc: cada aplicación de IA tenía su propia forma de llamar APIs, ejecutar funciones o leer archivos. MCP define un contrato común entre:

- **El cliente MCP** → la aplicación o agente que usa el LLM (ej. Claude Desktop, un agente LangGraph)
- **El servidor MCP** → el proceso que expone herramientas, prompts y recursos al cliente

```bash
┌─────────────────────┐        MCP Protocol         ┌─────────────────────┐
│    Cliente MCP      │ ◄──────────────────────────► │    Servidor MCP     │
│  (Agente / LLM app) │    (stdio / SSE / HTTP)      │  (tools, prompts,   │
└─────────────────────┘                              │      resources)     │
                                                     └─────────────────────┘
```

### Transportes disponibles

| Transporte | Cuándo usarlo |
|---|---|
| `stdio` | Proceso local — el cliente lanza el servidor como subproceso |
| `sse` | Servidor remoto — comunicación por HTTP con Server-Sent Events |

---

## La librería: `FastMCP`

Este proyecto usa **`FastMCP`**, la forma más sencilla de crear servidores MCP en Python. Viene incluida en el paquete `mcp`.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NombreDelServidor")
```

Con esa sola línea tienes un servidor MCP listo. Luego registras capacidades usando decoradores y al final lo arrancas:

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")   # o "sse"
```

`FastMCP` se encarga de:

- Serializar/deserializar los mensajes del protocolo
- Publicar el esquema de cada herramienta al cliente
- Gestionar el ciclo de vida de la sesión

---

## Las 3 primitivas de un servidor MCP

### 1. `@mcp.tool()` — Herramientas

Las **tools** son funciones que el LLM puede **invocar** para realizar acciones o cálculos. Son el equivalente al *function calling* de OpenAI, pero estandarizadas en MCP.

El LLM decide cuándo llamarlas basándose en el nombre y el docstring. Por eso ambos deben ser descriptivos.

```python
# servers/math_server.py

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b
```

```python
# servers/weather_server.py

@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return "Hot as hell"
```

> Las tools pueden ser síncronas o `async`. Los tipos de los parámetros se convierten automáticamente en JSON Schema para que el LLM sepa cómo llamarlas.

**¿Cuándo usar tools?**

- Llamadas a APIs externas
- Operaciones de cómputo (matemáticas, transformaciones)
- Lectura/escritura de archivos o bases de datos
- Cualquier acción con efecto secundario que el LLM deba poder disparar

---

### 2. `@mcp.prompt()` — Prompts

Los **prompts** son **plantillas de instrucciones reutilizables** que configuran el comportamiento del asistente para una tarea específica. El cliente puede pedirle al servidor que le entregue un prompt por nombre, y usarlo como system message o instrucción inicial.

```python
# servers/math_server.py

@mcp.prompt()
def math_assistant_prompt() -> str:
    """A prompt that configures the assistant to solve math problems step by step"""
    return (
        "You are a math assistant. "
        "When solving problems, use the available tools (add, multiply) "
        "and explain each step clearly."
    )
```

```python
# servers/weather_server.py

@mcp.prompt()
def weather_assistant_prompt(location: str) -> str:
    """A prompt that asks for a weather report for a given location"""
    return f"Please provide a weather report for {location} using the available tools."
```

> Los prompts pueden recibir parámetros (como `location`) para generar instrucciones dinámicas.

**¿Cuándo usar prompts?**

- Para encapsular instrucciones de sistema complejas y reutilizarlas
- Cuando distintas partes de tu app necesitan el mismo comportamiento del LLM
- Para que el servidor (y no el cliente) controle cómo debe comportarse el asistente

---

### 3. `@mcp.resource(uri)` — Recursos

Los **resources** son datos que el servidor expone al cliente mediante una **URI**. A diferencia de las tools, los recursos son de solo lectura y el cliente (o el LLM) los consulta para obtener contexto adicional.

```python
# servers/math_server.py

@mcp.resource("math://formulas")
def math_formulas() -> str:
    """Provides common math formulas"""
    return (
        "Common Math Formulas:\n"
        "- Area of circle: π * r²\n"
        "- Pythagorean theorem: a² + b² = c²\n"
        "- Area of rectangle: width * height\n"
        "- Area of triangle: (base * height) / 2\n"
        "- Sum of arithmetic series: n * (a1 + an) / 2"
    )
```

```python
# servers/weather_server.py

@mcp.resource("weather://supported-locations")
def supported_locations() -> str:
    """List of supported locations for weather queries"""
    return (
        "Supported locations:\n"
        "- New York\n"
        "- London\n"
        "- Tokyo\n"
        "- Paris\n"
        "- Sydney"
    )
```

> La URI puede ser cualquier cadena con formato `scheme://path`. Es buena práctica usar un scheme propio del dominio (`math://`, `weather://`, `db://`, etc.).

**¿Cuándo usar resources?**

- Documentación, catálogos o configuraciones que el LLM necesita como contexto
- Datos estáticos o semestáticos (listas de opciones válidas, esquemas, FAQs)
- Contenido que no requiere parámetros de entrada ni tiene efectos secundarios

---

## Resumen comparativo

| Primitiva | ¿Qué hace? | ¿Quién lo invoca? | ¿Tiene efectos? |
|---|---|---|---|
| `tool` | Ejecuta una acción o cómputo | El LLM (decide cuándo) | Sí |
| `prompt` | Devuelve una plantilla de instrucciones | El cliente / la app | No |
| `resource` | Expone datos por URI | El cliente / el LLM | No |

---

## Estructura del proyecto

```bash
mcp-crash-course/
├── main.py                  # Cliente MCP: conecta al math_server y lanza un agente
├── pyproject.toml           # Dependencias del proyecto
├── servers/
│   ├── __init__.py
│   ├── math_server.py       # Servidor MCP con tools de suma y multiplicación
│   └── weather_server.py    # Servidor MCP con tool de clima (transporte SSE)
```

### `main.py` — el cliente

Demuestra cómo conectarse a un servidor MCP desde Python usando `langchain-mcp-adapters` y `langgraph`:

1. Define los parámetros del servidor (`StdioServerParameters`)
2. Abre una sesión MCP con `stdio_client` + `ClientSession`
3. Carga las tools del servidor con `load_mcp_tools(session)`
4. Crea un agente ReAct con `create_react_agent(llm, tools)`
5. Invoca el agente con una pregunta en lenguaje natural

```python
result = await agent.ainvoke({"messages": [HumanMessage(content="What is 54 + 2 * 3?")]})
```

El agente resuelve la expresión llamando a `multiply(2, 3)` y luego `add(54, 6)` usando las tools del servidor.

---

## Instalación

### Requisitos

- Python ≥ 3.12
- Una API key de OpenAI

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd mcp-crash-course

# 2. Instalar dependencias (con uv — recomendado)
uv sync

# o con pip
pip install -e .

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env y añadir:
# OPENAI_API_KEY=sk-...
```

---

## Ejecución

```bash
python main.py
```

Esto arrancará el `math_server.py` como subproceso (transporte `stdio`), inicializará la sesión MCP, cargará las tools disponibles y ejecutará el agente con la pregunta de ejemplo.

---

## Crear tu propio servidor MCP

### Paso 1 — Crear el archivo del servidor

```python
# servers/mi_servidor.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MiServidor")
```

### Paso 2 — Añadir tools

```python
@mcp.tool()
def saludar(nombre: str) -> str:
    """Saluda a una persona por su nombre"""
    return f"Hola, {nombre}!"
```

### Paso 3 — (Opcional) Añadir un prompt

```python
@mcp.prompt()
def asistente_amigable() -> str:
    """Configura el asistente para responder de forma amigable"""
    return "Eres un asistente muy amigable. Responde siempre con entusiasmo."
```

### Paso 4 — (Opcional) Añadir un resource

```python
@mcp.resource("miservidor://info")
def info() -> str:
    """Información sobre el servidor"""
    return "Este servidor puede saludar personas."
```

### Paso 5 — Arrancar el servidor

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")   # para uso local
    # mcp.run(transport="sse")   # para uso remoto
```

### Paso 6 — Conectar desde el cliente

En `main.py`, apunta los parámetros al nuevo servidor:

```python
stdio_server_params = StdioServerParameters(
    command="python",
    args=["servers/mi_servidor.py"],
)
```

---

## Dependencias principales

| Paquete | Rol |
|---|---|
| `mcp` | Implementación del protocolo MCP (`FastMCP`, `ClientSession`, etc.) |
| `langchain-mcp-adapters` | Adaptador para cargar tools MCP en LangChain (`load_mcp_tools`) |
| `langchain-openai` | Integración de OpenAI con LangChain |
| `langgraph` | Motor de agentes ReAct (`create_react_agent`) |
| `python-dotenv` | Carga de variables de entorno desde `.env` |

---

## Referencias

- [Documentación oficial de MCP](https://modelcontextprotocol.io)
- [Especificación del protocolo](https://spec.modelcontextprotocol.io)
- [FastMCP en GitHub](https://github.com/jlowin/fastmcp)
- [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
