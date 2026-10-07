// The fog of war, drawn as fog in the air: a pass over the whole screen after everything else,
// which marches each pixel's ray back from the surface it hit towards the camera through a
// field of fog and thickens the pixel by how much fog the ray passed through. The fog is dense
// where the active unit makes little out and absent where it sees clearly, lies on the ground
// and thins with height, so pieces stand in it, a bluff rises through it, and a clear hex seen
// past a bank of it picks up a little haze on the way. The clarity per hex is the rules'
// (Sight.Survey), handed over as a texture one texel per hex (SightField) with the ground
// height beside it, sampled with linear filtering so the fog eases between hexes.
//
// Nothing is hidden by this pass: a piece the unit cannot see is not in the scene at all. The
// fog only says how well what is there is made out, and it caps short of opaque so the ground
// stays legible as a map under it.
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

// How much fog a metre of ray picks up at ground level where nothing is made out; it falls
// off with height above the ground over fog_height metres. Set so that a look down at
// fifty degrees through fog over unseen ground comes out thick before the cap, and a look
// along the ground through the same fog is thicker still.
uniform float fog_density = 0.4;
uniform float fog_height = 5.0;

// The ray is marched this far back from the surface towards the camera, in this many steps;
// fog further from the surface than that is above the camera's usual height anyway.
uniform float march_metres = 80.0;
const int STEPS = 24;

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

// Clarity and ground height at a point on the ground, bilinear in axial space.
vec2 sample_field(vec2 p) {
	vec2 size = vec2(textureSize(field, 0));
	vec2 uv = (axial_of(p) - vec2(field_origin) + 0.5) / size;
	return texture(field, uv).rg;
}

// The fog at a point in the air: nothing where the hex is clear, growing on the square of
// the murk so a hex mostly made out stays mostly clear, thinning with height above its ground.
float density_at(vec3 p) {
	vec2 f = sample_field(p.xz);
	float murk = 1.0 - clamp(f.x, 0.0, 1.0);
	float above = max(0.0, p.y - f.y);
	return fog_density * murk * murk * exp(-above / fog_height);
}

void fragment() {
	// The far side of the sky is at infinity in reversed depth; hold it to something finite.
	float depth = max(texture(depth_texture, SCREEN_UV).x, 0.00001);
	vec3 ndc = vec3(SCREEN_UV * 2.0 - 1.0, depth);
	vec4 view = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	view.xyz /= view.w;
	vec3 hit = (INV_VIEW_MATRIX * vec4(view.xyz, 1.0)).xyz;

	vec3 camera = INV_VIEW_MATRIX[3].xyz;
	vec3 ray = hit - camera;
	float distance = length(ray);
	vec3 dir = ray / max(distance, 0.001);
	if (distance > 300.0) {
		hit = camera + dir * 300.0;
		distance = 300.0;
	}

	// March back from the surface towards the camera, the start dithered per pixel so the
	// steps do not band.
	float span = min(distance, march_metres);
	float step = span / float(STEPS);
	float jitter = fract(52.9829189 * fract(dot(FRAGCOORD.xy, vec2(0.06711056, 0.00583715))));
	float optical = 0.0;
	for (int i = 0; i < STEPS; i++) {
		vec3 p = hit - dir * ((float(i) + jitter) * step);
		optical += density_at(p) * step;
	}
	float amount = fog_cap * (1.0 - exp(-optical));

	vec3 scene = max(texture(screen_texture, SCREEN_UV).rgb, vec3(0.0));
	vec3 gamma = pow(scene, vec3(1.0 / 2.2));
	gamma = mix(gamma, fog_colour, amount);
	ALBEDO = pow(gamma, vec3(2.2));
	ALPHA = 1.0;
}
