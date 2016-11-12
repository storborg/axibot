# Refactoring

- Pass configuration parameters directly from top-level: don't use Python
  module space for configuration.
- Use consistent terminology for intermediate variables. "Transits" is a
  terrible world.
- Add units to the docstring of any function that accepts or returns numeric
  values.
- Tests, tests, tests.

# Performance

- Better cornering velocity calculation.

# Features

- Add interface for configuring the start/stop height of pen servo.
- Add interface and/or infrastructure for pen changes.
- Color matching and/or layer assignment.


-------

# Steps

1. Extract paths from SVG --> [Path, Path, ...]

2. Subdivide paths to segments. --> [segment, segment, ...]

3. Add pen-up segments --> [(segment, pen_up), (segment, pen_up), ...]

4. Convert inches to steps --> [(segment, pen_up), ...]

5. Plan velocity limits -> [(tagged_segment, pen_up), ...]

6. Plan actions -> [action, action, ...]
