#ifdef GL_ES
precision highp float;
#endif

varying vec4 frag_color;
varying vec2 tex_coord0;

uniform sampler2D texture0;

uniform vec2 resolution;
uniform float time;

void main() {
    gl_FragColor = texture2D(texture0, tex_coord0);
}
