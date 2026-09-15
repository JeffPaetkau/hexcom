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

varying vec3 world_pos;

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

	ALBEDO = colour;
	ROUGHNESS = base_roughness - 0.08 * grain - 0.15 * fleck_mask;
	SPECULAR = 0.35;
}
