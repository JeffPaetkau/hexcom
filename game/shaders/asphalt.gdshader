// Asphalt, procedurally, in world coordinates: no image, no tiling, no seam, so the plain can
// be as large as the camera can see. Three scales of value noise stand in for wear patches,
// surface unevenness and aggregate grain, plus sparse bright flecks of stone.
//
// Every octave fades out as its cells shrink below a pixel, so the grain never sparkles at
// distance; the average of each octave is zero, so fading one out does not shift the tone.

shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec3 dark : source_color = vec3(0.12, 0.12, 0.125);
uniform vec3 light : source_color = vec3(0.30, 0.30, 0.31);
uniform vec3 fleck : source_color = vec3(0.55, 0.54, 0.52);
uniform float grain_cells_per_metre = 12.0;
uniform float mottle_metres = 9.0;
uniform float base_roughness : hint_range(0.0, 1.0) = 0.9;

// The hex grid, drawn in the same world coordinates so it is as endless as the plain. Flat-
// topped, hex_size metres centre to corner: the same layout as Hex.cs, and it must stay so.
// Off by default: the grid is how the game works, not something it shows. Raise the strength
// to check that what the board draws lines up with what the rules think.
uniform float hex_size = 1.0;
uniform vec3 grid_colour : source_color = vec3(0.62, 0.62, 0.64);
uniform float grid_width = 0.03;
uniform float grid_strength : hint_range(0.0, 1.0) = 0.0;

varying vec3 world_pos;

// Centre of the hex containing p, by rounding fractional axial coordinates.
vec2 hex_centre(vec2 p) {
	float q = 2.0 / 3.0 * p.x / hex_size;
	float r = (-1.0 / 3.0 * p.x + 0.57735027 * p.y) / hex_size;
	float s = -q - r;
	float rq = round(q);
	float rr = round(r);
	float rs = round(s);
	float dq = abs(rq - q);
	float dr = abs(rr - r);
	float ds = abs(rs - s);
	if (dq > dr && dq > ds) {
		rq = -rr - rs;
	} else if (dr > ds) {
		rr = -rq - rs;
	}
	return vec2(hex_size * 1.5 * rq, hex_size * 1.7320508 * (rr + rq / 2.0));
}

// Distance from a point (as an offset from its hex centre) to the nearest edge of the hex.
float hex_edge_distance(vec2 d) {
	float apothem = hex_size * 0.8660254;
	float m = 0.0;
	for (int k = 0; k < 3; k++) {
		float a = radians(30.0 + 60.0 * float(k));
		m = max(m, abs(dot(d, vec2(cos(a), sin(a)))));
	}
	return apothem - m;
}

float hash12(vec2 p) {
	vec3 p3 = fract(vec3(p.xyx) * 0.1031);
	p3 += dot(p3, p3.yzx + 33.33);
	return fract((p3.x + p3.y) * p3.z);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	float a = hash12(i);
	float b = hash12(i + vec2(1.0, 0.0));
	float c = hash12(i + vec2(0.0, 1.0));
	float d = hash12(i + vec2(1.0, 1.0));
	return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

// Three octaves, each centred on zero and faded by its screen footprint. Roughly -0.3..0.3.
float fbm(vec2 p) {
	float sum = 0.0;
	float amp = 0.5;
	float norm = 0.0;
	for (int i = 0; i < 3; i++) {
		float footprint = length(fwidth(p));
		float fade = clamp(1.5 - footprint, 0.0, 1.0);
		sum += amp * (vnoise(p) - 0.5) * fade;
		norm += amp;
		p = p * 2.03 + vec2(17.3, 9.1);
		amp *= 0.5;
	}
	return sum / norm;
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = world_pos.xz;

	float mottle = fbm(p / mottle_metres);
	float medium = fbm(p);
	float grain = fbm(p * grain_cells_per_metre);

	// Unsmoothed per-cell grit at a few centimetres, for the sandy sharpness value noise lacks.
	// Two lattices, one turned 37 degrees, so the cells do not read as a square grid.
	vec2 gp = p * grain_cells_per_metre * 2.5;
	vec2 gq = mat2(vec2(0.7986, 0.6018), vec2(-0.6018, 0.7986)) * gp;
	float grit_fade = clamp(1.5 - length(fwidth(gp)), 0.0, 1.0);
	float grit = (hash12(floor(gp)) + hash12(floor(gq)) - 1.0) * 0.7 * grit_fade;

	float tone = 0.5 + 0.35 * mottle + 0.25 * medium + 0.5 * grain + 0.3 * grit;
	vec3 colour = mix(dark, light, clamp(tone, 0.0, 1.0));

	float fleck_mask = step(0.988, hash12(floor(gp) + vec2(0.5, 0.5))) * grit_fade;
	colour = mix(colour, fleck, fleck_mask * 0.4);

	// Grid lines: anti-aliased by their screen footprint, and faded out altogether once a
	// line would be thinner than a pixel, so the far plain does not shimmer.
	float edge = hex_edge_distance(p - hex_centre(p));
	float edge_fw = fwidth(edge);
	float line = 1.0 - smoothstep(grid_width - edge_fw, grid_width + edge_fw, edge);
	line *= clamp(1.0 - edge_fw / 0.25, 0.0, 1.0);
	colour = mix(colour, grid_colour, line * grid_strength);

	ALBEDO = colour;
	ROUGHNESS = base_roughness - 0.08 * grain - 0.15 * fleck_mask;
	SPECULAR = 0.35;
}
