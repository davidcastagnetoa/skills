---
name: random_challenge_sequencer
description: Generar secuencias aleatorias de desafíos de liveness para prevenir ataques de replay grabado
type: Algorithm
priority: Esencial
mode: Self-hosted
---

# random_challenge_sequencer

Genera una secuencia aleatoria e imprevisible de challenges activos para cada sesión, haciendo imposible que un atacante grabe y reproduzca la respuesta correcta.

## When to use

Usar al inicio de cada sesión de liveness para determinar qué challenges se solicitarán al usuario.

## Instructions

1. Definir el pool de challenges disponibles: `['blink_2x', 'turn_left', 'turn_right', 'smile', 'nod']`.
2. Para cada sesión, seleccionar aleatoriamente 2-3 challenges: `selected = random.sample(pool, k=2)`.
3. Usar `secrets.SystemRandom()` (no `random.random()`) para mayor entropía criptográfica.
4. Incluir el timestamp y session_id en la semilla para que la secuencia sea irrepetible.
5. Almacenar la secuencia esperada en Redis con TTL de 120 segundos: `SETEX session:{id}:challenges 120 {challenges}`.
6. El frontend recibe los challenges encriptados; no en texto plano.
7. Validar que cada challenge se completa en el orden correcto.

## Notes

- Rotar el pool de challenges periódicamente para evitar que atacantes conozcan todas las opciones.
- No reusar la misma secuencia aunque el usuario repita la sesión.