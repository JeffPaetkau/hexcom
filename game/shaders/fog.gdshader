// The fog of war, drawn as fog: a pass over the whole screen after everything else, which fogs
// each pixel by how poorly the active unit makes out the hex under it. The clarity per hex is
// the rules' (Sight.Survey), handed over as a texture one texel per hex (SightField) with the
// ground height beside it, and it is sampled with linear filtering and a few taps either way so
// the fog eases from one area to the next rather than stepping at hex edges.
//
// Nothing is hidden by this pass: a piece the unit cannot see is not in the scene at all. The
// fog only says how well what is there is made out, and it caps short of opaque so the ground
// stays legible as a map under it. Fog thins with height above the ground, so tall things
// stand up out of it.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, fog_disabled, shadows_disabled;

uniform sampler2D depth_texture : hint_depth_texture, filter_nearest, repeat_disable;
uniform sampler2D screen_texture : hint_screen_texture, filter_nearest, repeat_disable;

// R is clarity, G the ground height at the hex centre; indexed by axial coordinate from field_origin.
uniform sampler2D field : filter_linear, repeat_disable;
uniform ivec2 field_origin = ivec2(0, 0);
uniform float hex_size = 0.57735027;

// The horizon's colour, as the palette gives it (sRGB, not converted): the blend is done in
// that space, where a strength of a half looks like a half. Blended in linear light a pale
// fog over dark grass swamps it at any strength worth seeing, as the hex marks found.
uniform vec3 fog_colour = vec3(0.72, 0.79, 0.90);
uniform float fog_cap : hint_range(0.0, 1.0) = 0.75;
uniform float fog_height = 6.0;
uniform float blur = 1.0;

void vertex() {
	// The whole screen, at the near plane (depth runs from one at the near plane to nothing far off).
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

// Fractional axial coordinates of a point on the ground plane: the same map as Hex.At before rounding.
vec2 axial_of(vec2 p) {
	float q = 2.0 / 3.0 * p.x / hex_size;
	float r = (-1.0 / 3.0 * p.x + 0.57735027 * p.y) / hex_size;
	return vec2(q, r);
}

// Clarity and ground height at a point, bilinear in axial space and blurred a texel each way.
vec2 sample_field(vec2 axial) {
	vec2 size = vec2(textureSize(field, 0));
	vec2 uv = (axial - vec2(field_origin) + 0.5) / size;
	vec2 dq = vec2(blur, 0.0) / size;
	vec2 dr = vec2(0.0, blur) / size;
	vec2 sum = 2.0 * texture(field, uv).rg;
	sum += texture(field, uv + dq).rg;
	sum += texture(field, uv - dq).rg;
	sum += texture(field, uv + dr).rg;
	sum += texture(field, uv - dr).rg;
	return sum / 6.0;
}

void fragment() {
	float depth = texture(depth_texture, SCREEN_UV).x;
	if (depth < 0.00001) {
		// The sky.
		ALBEDO = fog_colour;
		ALPHA = 0.0;
	} else {
		vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, depth);
		vec4 view = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
		view.xyz /= view.w;
		vec4 world = INV_VIEW_MATRIX * vec4(view.xyz, 1.0);

		vec2 f = sample_field(axial_of(world.xz));
		float clarity = clamp(f.x, 0.0, 1.0);
		float above = max(0.0, world.y - f.y);
		float amount = fog_cap * (1.0 - clarity) * exp(-above / fog_height);

		vec3 scene = max(texture(screen_texture, SCREEN_UV).rgb, vec3(0.0));
		vec3 gamma = pow(scene, vec3(1.0 / 2.2));
		gamma = mix(gamma, fog_colour, amount);
		ALBEDO = pow(gamma, vec3(2.2));
		ALPHA = 1.0;
	}
}
