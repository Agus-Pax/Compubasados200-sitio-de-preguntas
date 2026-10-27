# Compubasados200-sitio-de-preguntas
Integrantes: Agustín Paz, Lautaro Heredia, Melina Devetak, Santiago Ross

Patrones implementados en el diagrama: strategy y factory method
Se implemento el patrón factory method para la creación de respuestas las cuales son asociadas a una pregunta. El patrón strategy se implementa dentro de la fabrica concreta, el factory method toma como parametro una enumeración para poder decidir que tipo de respuesta se genera, si es Manual o Humana, entonces la fabrica usara la estrategia manual, si es generada o por agente, la fabrica generara una respuesta usando la estrategia generada disponible(ChatGPT, Gemini, Claude o agente local).
