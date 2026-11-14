#version 440
// The spiral spreads (Uzumaki): hand-inked spirals creep in from the screen's corners and
// edges as `level` rises from 0 (fresh boot) to 1 (hours awake). Each colony wakes up at its
// own level, grows a ragged front and slowly winds inward. Output is premultiplied ink.
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float time;     // seconds
    float level;    // 0..1
    float aspect;   // width / height
};

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
    for (int i = 0; i < 4; i++) { v += a * vnoise(p); p = p * 2.07 + 11.3; a *= 0.5; }
    return v;
}

const int NC = 7;
const float TAU = 6.2831853;

void main() {
    vec2 p = vec2(qt_TexCoord0.x * aspect, qt_TexCoord0.y);
    float A = aspect;
    // colonies: position (screen-height units), wake level, max radius, arms, turn direction
    vec2  pos[NC]  = vec2[](vec2(-0.03, -0.04), vec2(A + 0.04, 1.03), vec2(A + 0.03, -0.03),
                            vec2(-0.04, 1.04), vec2(-0.07, 0.52), vec2(A + 0.06, 0.46),
                            vec2(A * 0.5, -0.13));
    float wake[NC] = float[](0.00, 0.12, 0.26, 0.40, 0.55, 0.68, 0.80);
    float rmax[NC] = float[](0.66, 0.60, 0.52, 0.50, 0.44, 0.44, 0.38);
    float arms[NC] = float[](1.0, 2.0, 1.0, 1.0, 2.0, 1.0, 1.0);
    float dirn[NC] = float[](1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0);
    float pitch[NC] = float[](0.034, 0.040, 0.031, 0.036, 0.042, 0.033, 0.030);

    float ink = 0.0;
    float blood = 0.0;
    for (int i = 0; i < NC; i++) {
        float g = smoothstep(wake[i], wake[i] + 0.32, level);
        if (g <= 0.0) continue;
        vec2 v = p - pos[i];
        float r = length(v);
        float R = rmax[i] * g;
        if (r > R * 1.35) continue;
        float th = atan(v.y, v.x);
        float fi = float(i);
        // ragged, creeping front
        float front = R * (0.78 + 0.42 * fbm(vec2(th * 2.2 + fi * 7.1, fi * 3.3 + time * 0.004)));
        // hand-inked wobble
        float rw = r + 0.006 * sin(7.0 * th + r * 33.0 + fi) + 0.005 * (vnoise(vec2(th * 5.0, r * 18.0)) - 0.5);
        float ph = rw / pitch[i] - dirn[i] * arms[i] * th / TAU + time * 0.018 * dirn[i];
        float line = pow(0.5 + 0.5 * cos(TAU * ph), 16.0);
        float dry = 0.45 + 0.55 * vnoise(vec2(th * 38.0 + fi, r * 70.0));     // dry-brush breaks
        float fade = 1.0 - smoothstep(front * 0.55, front, r);
        float core = smoothstep(0.012, 0.05, r);
        float age = 0.35 + 0.65 * g;
        ink = max(ink, line * dry * fade * core * age);
        if (i == 0) blood = smoothstep(0.86, 1.0, level) * (1.0 - smoothstep(0.0, R * 0.32, r)) * line;
    }
    vec3 col = mix(vec3(0.66), vec3(0.42, 0.03, 0.03), clamp(blood * 1.6, 0.0, 1.0));
    float a = clamp(max(ink * 0.40, blood * 0.55), 0.0, 1.0);
    fragColor = vec4(col * a, a) * qt_Opacity;
}
