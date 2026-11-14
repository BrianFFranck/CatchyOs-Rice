#version 440
// Ink-bleed reveal of the incoming desktop's video (used as layer.effect on that video).
// progress 0 -> nothing shown, 1 -> fully shown. The edge is a ragged, wet ink front that
// darkens both sides as it soaks outward from `origin`.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float progress;
    float seed;
    float aspect;
    vec2 origin;
};
layout(binding = 1) uniform sampler2D source;

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}
float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x),
               mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y);
}
float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; }
    return v;
}

void main() {
    vec2 uv = qt_TexCoord0;
    vec2 p = vec2(uv.x * aspect, uv.y);
    vec2 o = vec2(origin.x * aspect, origin.y);
    float maxd = length(vec2(aspect, 1.0)) + 0.1;
    float d = distance(p, o) / maxd;
    // capillary fingers: big slow blobs plus fine fibres, like ink soaking into paper
    float n = fbm(p * 2.6 + seed * 13.0) * 0.75 + fbm(p * 11.0 - seed * 7.0) * 0.25;
    float field = d * 0.62 + n * 0.48;
    float thr = mix(-0.05, 1.12, progress);

    float inside = 1.0 - smoothstep(thr - 0.004, thr + 0.004, field);
    float wet = 1.0 - smoothstep(0.0, 0.05, thr - field);        // just behind the front
    float halo = (1.0 - smoothstep(0.0, 0.06, field - thr)) * (1.0 - inside); // just ahead of it

    vec4 c = texture(source, uv);
    c.rgb *= 1.0 - 0.88 * wet * inside;
    float a = max(inside, halo * 0.7);
    vec3 col = c.rgb * inside;                       // halo is pure ink (black)
    fragColor = vec4(col, a) * qt_Opacity;
}
