// The ground surface, in world coordinates: grass, dirt and asphalt decided per pixel from a
// baked map of distances to the roads, the slope, and noise. No image textures; the grain of
// every surface is procedural, faded out as its cells drop below a pixel so nothing shimmers.
//
// Distances in the map are signed and measured from the road EDGE, negative on the road, so a
// threshold at zero is the edge itself and the shoulder is a second threshold a few metres out.

shader_type spatial;
render_mode cull_disabled, diffuse_burley, specular_schlick_ggx;

uniform sampler2D surface_map : filter_linear, repeat_disable;
uniform float map_half_extent = 1024.0;

uniform vec3 grass_dark : source_color = vec3(0.15, 0.23, 0.08);
uniform vec3 grass_light : source_color = vec3(0.42, 0.45, 0.19);
uniform vec3 dirt_dark : source_color = vec3(0.24, 0.18, 0.12);
uniform vec3 dirt_light : source_color = vec3(0.5, 0.42, 0.3);
uniform vec3 asphalt_dark : source_color = vec3(0.12, 0.12, 0.125);
uniform vec3 asphalt_light : source_color = vec3(0.30, 0.30, 0.31);
uniform vec3 fleck : source_color = vec3(0.55, 0.54, 0.52);

// The hex grid, never shown in play. Raise the strength to check that what the board draws
// lines up with what the rules think the hexes are. Flat-topped, hex_size centre to corner;
// the game sets it from the rules (Units.HexSize) at start, the default only matches.
uniform float hex_size = 0.57735027;
uniform vec3 grid_colour : source_color = vec3(0.85, 0.85, 0.87);
uniform float grid_width = 0.02;
uniform float grid_strength : hint_range(0.0, 1.0) = 0.0;

// Marks on hexes, painted here rather than built as meshes so nothing can poke through them:
// one texel per hex, colour and strength, indexed by axial coordinate from marks_origin. The
// game fills it (HexMarks); the disc drawn about each marked centre is mark_radius across.
uniform sampler2D marks : filter_nearest, repeat_disable, hint_default_transparent;
uniform ivec2 marks_origin = ivec2(0, 0);
uniform float mark_radius = 0.46;

varying vec3 world_pos;
varying vec3 world_normal;

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

// The hex under a point, in axial coordinates: the same rounding as Hex.At in the rules.
ivec2 hex_axial(vec2 p) {
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
	return ivec2(int(rq), int(rr));
}

vec2 hex_centre_of(ivec2 axial) {
	float rq = float(axial.x);
	float rr = float(axial.y);
	return vec2(hex_size * 1.5 * rq, hex_size * 1.7320508 * (rr + rq / 2.0));
}

float hex_edge_distance(vec2 d) {
	float apothem = hex_size * 0.8660254;
	float m = 0.0;
	for (int k = 0; k < 3; k++) {
		float a = radians(30.0 + 60.0 * float(k));
		m = max(m, abs(dot(d, vec2(cos(a), sin(a)))));
	}
	return apothem - m;
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec2 p = world_pos.xz;

	// Distances to the roads in metres, from the map; off the map there are none.
	vec2 uv = (p + vec2(map_half_extent)) / (2.0 * map_half_extent);
	vec4 map = texture(surface_map, uv);
	float paved_edge = map.r;
	float track_edge = map.g;
	if (any(lessThan(uv, vec2(0.0))) || any(greaterThan(uv, vec2(1.0)))) {
		paved_edge = 20.0;
		track_edge = 20.0;
	}

	// Grass: broad patches of dry and lush, a metre-scale tussock pattern, fine blades.
	float g_patch = fbm(p / 14.0);
	float g_tuft = fbm(p * 1.2);
	float g_blade = fbm(p * 9.0);
	vec3 grass = mix(grass_dark, grass_light, clamp(0.45 + 0.9 * g_patch + 0.5 * g_tuft + 0.5 * g_blade, 0.0, 1.0));

	// Dirt: mottled, with a little grit.
	float d_mottle = fbm(p / 5.0);
	float d_grit = fbm(p * 7.0);
	vec3 dirt = mix(dirt_dark, dirt_light, clamp(0.5 + 0.8 * d_mottle + 0.5 * d_grit, 0.0, 1.0));

	// Asphalt, as the plain had it.
	float a_mottle = fbm(p / 9.0);
	float a_medium = fbm(p);
	float a_grain = fbm(p * 12.0);
	vec2 gp = p * 30.0;
	vec2 gq = mat2(vec2(0.7986, 0.6018), vec2(-0.6018, 0.7986)) * gp;
	float grit_fade = clamp(1.5 - length(fwidth(gp)), 0.0, 1.0);
	float grit = (hash12(floor(gp)) + hash12(floor(gq)) - 1.0) * 0.7 * grit_fade;
	float a_tone = 0.5 + 0.35 * a_mottle + 0.25 * a_medium + 0.5 * a_grain + 0.3 * grit;
	vec3 asphalt = mix(asphalt_dark, asphalt_light, clamp(a_tone, 0.0, 1.0));
	float fleck_mask = step(0.988, hash12(floor(gp) + vec2(0.5, 0.5))) * grit_fade;
	asphalt = mix(asphalt, fleck, fleck_mask * 0.4);

	// A worn white line just inside the paved edge.
	float line = 1.0 - smoothstep(0.0, 0.1, abs(paved_edge + 0.45) - 0.06);
	line *= clamp(1.0 - fwidth(paved_edge) / 0.15, 0.0, 1.0);
	line *= clamp(0.6 + 1.5 * fbm(p * 0.7), 0.0, 1.0);
	asphalt = mix(asphalt, vec3(0.78), line * 0.55);

	// Where the dirt shows: steep ground, bare patches, road shoulders, and the tracks.
	float slope = 1.0 - clamp(world_normal.y, 0.0, 1.0);
	float dirt_w = smoothstep(0.06, 0.16, slope);
	dirt_w = max(dirt_w, smoothstep(0.17, 0.23, fbm(p / 45.0) + 0.08 * fbm(p / 6.0)));
	dirt_w = max(dirt_w, 1.0 - smoothstep(1.0, 7.0, paved_edge + 6.0 * fbm(p / 11.0)));
	dirt_w = max(dirt_w, 1.0 - smoothstep(-0.6, 1.5, track_edge));
	dirt_w = clamp(dirt_w, 0.0, 1.0);

	float paved_w = 1.0 - smoothstep(-0.2, 0.2, paved_edge);

	vec3 colour = mix(grass, dirt, dirt_w);
	colour = mix(colour, asphalt, paved_w);

	// The mark on this hex, if any: a disc about the centre, its edge a pixel wide.
	ivec2 axial = hex_axial(p);
	vec2 centre = hex_centre_of(axial);
	ivec2 texel = axial - marks_origin;
	if (all(greaterThanEqual(texel, ivec2(0))) && all(lessThan(texel, textureSize(marks, 0)))) {
		vec4 mark = texelFetch(marks, texel, 0);
		float dist = length(p - centre);
		float dist_fw = fwidth(dist);
		float inside = 1.0 - smoothstep(mark_radius - dist_fw, mark_radius + dist_fw, dist);
		// Blended in gamma space, where a strength of a third looks like a third. In linear
		// light a bright mark over dark grass swamps it at any strength worth seeing.
		vec3 gamma = pow(colour, vec3(1.0 / 2.2));
		gamma = mix(gamma, mark.rgb, mark.a * inside);
		colour = pow(gamma, vec3(2.2));
	}

	float edge = hex_edge_distance(p - centre);
	float edge_fw = fwidth(edge);
	float grid = 1.0 - smoothstep(grid_width - edge_fw, grid_width + edge_fw, edge);
	grid *= clamp(1.0 - edge_fw / 0.25, 0.0, 1.0);
	colour = mix(colour, grid_colour, grid * grid_strength);

	ALBEDO = colour;
	ROUGHNESS = mix(mix(0.95, 0.9, dirt_w), 0.9 - 0.08 * a_grain, paved_w);
	SPECULAR = mix(0.2, 0.35, paved_w);
}
