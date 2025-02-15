import math
import glm

from pyglfw.libapi import *
from gl import *

from scripts import (
    ecs,
)

from systems.base_sys import System
from scripts.callbacks import *
from scripts.components import *


def euclidean(theta: float, phi: float):
    cosT = math.cos(theta)
    sinT = math.sin(theta)
    cosP = math.cos(phi)
    sinP = math.sin(phi)
    return glm.vec3(sinT * cosP, cosT, sinT * sinP)


class RenderSys(System):
    def init(self):
        self.callbacks = {
            CB_UPDATE: self.update,
            CB_WINDOW_RESIZE: self.on_window_size,
        }

        vertexShader = createShader(open('shaders/default.vert', 'r').read(), GL_VERTEX_SHADER)
        fragmentShader = createShader(open('shaders/default.frag', 'r').read(), GL_FRAGMENT_SHADER)

        waterVertexShader = createShader(open('shaders/water.vert', 'r').read(), GL_VERTEX_SHADER)

        self.shader = createPipeline([vertexShader, fragmentShader])
        self.waterShader = createPipeline([waterVertexShader, fragmentShader])

        self.w = 1
        self.h = 1

    def on_window_size(self, ecs_data: ecs.ECS, w: int, h: int):
        self.w = w
        self.h = h
        glViewport(0, 0, w, h)

    def update(self, ecs_data: ecs.ECS, dt):
        glUseProgram(self.shader)
        for cam_ent_id in ecs_data.get_entities(COMP_CAMERA, COMP_TRANSFORM):

            cam_data = ecs_data.get_component_data(cam_ent_id, COMP_CAMERA)
            trans_data = ecs_data.get_component_data(cam_ent_id, COMP_TRANSFORM)


            cam_pos = glm.vec3(trans_data[TRANSFORM_X:TRANSFORM_Z + 1])

            #glUniform3f(glGetUniformLocation(self.shader, 'cameraPosition'), cam_pos.x, cam_pos.y, cam_pos.z)

            view = glm.mat4(1.0)
            view = glm.translate(view, glm.vec3(0, 0, -cam_data[CAMERA_DIST]))
            view = glm.rotate(view, trans_data[TRANSFORM_PITCH], glm.vec3(1.0, 0.0, 0.0))
            view = glm.rotate(view, trans_data[TRANSFORM_YAW], glm.vec3(0.0, 1.0, 0.0))
            view = glm.translate(view, -cam_pos)

            # forward = euclidean(trans_data[TRANSFORM_YAW],
            #                     trans_data[TRANSFORM_PITCH])
            # view = glm.lookAt(cam_pos, cam_pos + forward, glm.vec3(0, 1, 0))

            proj = glm.perspective(cam_data[CAMERA_FOV],
                                   self.w / float(self.h),
                                   cam_data[CAMERA_NEAR],
                                   cam_data[CAMERA_FAR])

            for ent_id in ecs_data.get_entities(COMP_MESH):
                mesh_data = ecs_data.get_component_data(ent_id, COMP_MESH)
                vao_data = self.engine.assets.get_mesh_data(mesh_data[MESH_ID])

                activeShader = self.shader
                if mesh_data[MESH_SHADER_ID] == 1:
                    activeShader = self.waterShader
                else:
                    activeShader = self.shader

                glUseProgram(activeShader)

                if activeShader == self.waterShader:
                    glUniform1f(glGetUniformLocation(activeShader, 'time'), glfwGetTime())

                glUniformMatrix4fv(glGetUniformLocation(activeShader, 'view'), 1, GL_FALSE, glm.value_ptr(view))
                glUniformMatrix4fv(glGetUniformLocation(activeShader, 'proj'), 1, GL_FALSE, glm.value_ptr(proj))

                spec = mesh_data[MESH_SPEC_R: MESH_SPEC_B + 1]

                texHash = mesh_data[MESH_TEX_ID]

                if texHash is not -1:
                    tex = self.engine.assets.get_texture_data(texHash)
                    glBindTexture(GL_TEXTURE_2D, tex)
                    # glActiveTexture(GL_TEXTURE0 + tex)
                    glUniform1i(glGetUniformLocation(activeShader, 'albedoTexture'), 0)

                model = glm.mat4(1.0)

                trans_data = ecs_data.get_component_data(ent_id, COMP_TRANSFORM)
                if trans_data:
                    model_pos = glm.vec3(trans_data[TRANSFORM_X:TRANSFORM_Z + 1])
                    model_scale = glm.vec3(trans_data[TRANSFORM_SX:TRANSFORM_SZ + 1])
                    model = glm.translate(model, model_pos)
                    model = glm.rotate(model, trans_data[TRANSFORM_YAW], glm.vec3(0, 1, 0))
                    model = glm.scale(model, model_scale)

                glUniformMatrix4fv(glGetUniformLocation(activeShader, 'model'), 1, GL_FALSE, glm.value_ptr(model))

                for vao, index_count in vao_data:
                    glBindVertexArray(vao)
                    glDrawElements(GL_TRIANGLES, index_count, GL_UNSIGNED_INT, None)
