#!/usr/bin/env python
# -*- coding:utf-8 -*-

import shutil
import os
import sys
import re
import glob
import yaml
import jinja2
from wand.image import Image

class Config:
    def __init__(self, config_path):
        if not os.path.exists(config_path):
            raise ValueError('%s does not exist.' % config_path)

        # Init default attributes
        self.dir  = '.'
        self.imgs = []
        self.config_path = config_path

        self.abs_dir = self.get_abs_path(self.dir, os.path.dirname(self.config_path))
        self.parse_config()

    def parse_config(self):
        config_handler = open(self.config_path, 'r')
        content = config_handler.read()
        config_handler.close()

        config = yaml.load(content)
        
        for k, v in config.iteritems():
            setattr(self, k, v)

        if not self.imgs:
            raise ValueError('Missing "imgs" property.')

        for img in self.imgs:
            if not img.has_key('name'):
                raise ValueError('Missing "name" property in imgs.')

            if not img.has_key('files'):
                raise ValueError('Missing "files" property in imgs.')

            if not isinstance(img['files'], list):
                img['files'] = [img['files']]

            if not img.has_key('output') or img['output'] is True:
                img['output'] = img['name']

            if img['output'] is False:
                img['abs_output'] = None
            else:
                img['abs_output'] = self.get_abs_path(img['output'])

            if img.has_key('css'):
                if img['css'].has_key('output') and img['css'].has_key('template') and img['css']['output'] is not False:
                    img['css']['abs_output'] = self.get_abs_path(img['css']['output'])
                    img['css']['abs_template'] = self.get_abs_path(img['css']['template'])
                else:
                    img['css']['abs_output'] = None
                    img['css']['abs_template'] = None
            else:
                img['css'] = {
                    ouput: False,
                    template: None
                }

    def get_abs_path(self, path, rel_path = None):
        if not rel_path:
            rel_path = self.abs_dir # make sure self.abs_dir calculate first

        path = os.path.join(rel_path, path)
        return os.path.normpath(path) # remove useless dot, eg: /test/./test1.png


class SpriteImage:
    def __init__(self, img_path):
        self.img_path = img_path
        self.filename = os.path.basename(img_path)
        self.x = self.y = 0
        self.setted = False

        with Image(filename = img_path) as img:
            self.width, self.height = img.size


class SpriteCanvas:
    def __init__(self, width = 0, height = 0):
        self.width  = width
        self.height = height


class SpriteCandidate:
    def __init__(self, width = 0, height = 0, x = 0, y = 0):
        self.width  = width
        self.height = height
        self.x      = x
        self.y      = y


class Sprite:
    def __init__(self, config, img):
        self.config = config
        self.img = img

        self.candidates  = []
        self.canvas = SpriteCanvas()
        
        self.images_dict = {} # prevent repeat image
        self.images = self.get_images()
        
        self.unset_image_length = len(self.images)

    def render(self):
        if self.unset_image_length == 0:
            return
            
        self.gen_image()
        self.save_image()
        self.save_css_file()

    def get_images(self):
        images = []
        for globpath in self.img['files']:
            abs_globpath = os.path.join(self.config.abs_dir, globpath)
            for abs_img_path in glob.glob(abs_globpath):

                if abs_img_path == self.config.get_abs_path(self.img['output']):
                    continue
                    
                if self.images_dict.has_key(abs_img_path):
                    continue

                self.images_dict[abs_img_path] = True

                img = SpriteImage(abs_img_path)
                images.append(img)

        return images

    def gen_image(self):
        if self.unset_image_length == 0:
            return

        if self.candidates:
            candidate = self.candidates.pop()
            img = self.get_max_width_image()

            if img.width == candidate.width and img.height <= candidate.height:

                img.x = candidate.x
                img.y = candidate.y
                img.setted = True

                self.unset_image_length -= 1

                new_candidate_height = candidate.height - img.height

                if new_candidate_height > 0:
                    candidate_options = dict(
                        width = candidate.width,
                        height = new_candidate_height,
                        x = img.x,
                        y = img.y + img.height
                    )

                    self.candidates.append(SpriteCandidate(**candidate_options))

                self.gen_image()

            else:
                img = self.get_max_height_image()

                if img.width > candidate.width or img.height > candidate.height:
                    return self.gen_image()

                img.x = candidate.x
                img.y = candidate.y
                img.setted = True

                new_right_candidate_width = candidate.width - img.width

                if new_right_candidate_width > 0:
                    right_candidate_options = dict(
                        width = new_right_candidate_width,
                        height = img.height,
                        x = candidate.x + img.width,
                        y = candidate.y,
                    )
                    
                    self.candidates.append(SpriteCandidate(**right_candidate_options))

                new_bottom_condidate_height = candidate.height - img.height
                if new_bottom_condidate_height > 0:
                    bottom_candidate_options = dict(
                        width = candidate.width,
                        height = new_bottom_condidate_height,
                        x = candidate.x,
                        y = candidate.y + img.height
                    )

                    self.candidates.append(SpriteCandidate(**bottom_candidate_options))

                self.unset_image_length -=1
                self.gen_image()

        else:
            if self.canvas.height == 0:
                img = self.get_max_width_image()
                img.x = img.y = 0
                img.setted = True

                self.canvas.width = img.width
                self.canvas.height = img.height

                self.unset_image_length -= 1

            if self.unset_image_length > 0:
                
                img = self.get_max_width_image()

                if img.width == self.canvas.width:
                    img.x = 0
                    img.y = self.canvas.height
                    img.setted = True

                    self.canvas.height += img.height
                    self.unset_image_length -= 1

                    self.gen_image()
                else:
                    img = self.get_max_height_image()

                    img.x = 0
                    img.y = img.y = self.canvas.height
                    img.setted = True

                    candidate_options = dict(
                        width = self.canvas.width - img.width,
                        height = img.height,
                        x = img.width,
                        y = self.canvas.height
                    )
                    
                    self.candidates.append(SpriteCandidate(**candidate_options))

                    self.canvas.height += img.height
                    self.unset_image_length -= 1

                    self.gen_image()

    def save_image(self):
        if not self.img['output']:
            return

        with Image(width = self.canvas.width, height = self.canvas.height) as gen_img:
            for img in self.images:
                with Image(filename = img.img_path) as sub_img:
                    gen_img.composite(sub_img, left = img.x, top = img.y)

            gen_img.save(filename = self.img['abs_output'])

    def save_css_file(self):
        if not self.img['css']['abs_template'] or not self.img['css']['abs_output']:
            return

        css_canvas = CssCanvas(self.canvas)
        css_images = []

        for img in self.images:
            css_images.append(CssImage(img))


        template_handler = open(self.img['css']['abs_template'], 'r')
        template_content = template_handler.read()
        template_handler.close()

        css_output = jinja2.Template(template_content).render(
            canvas = css_canvas,
            images = css_images
        )

        output_handler = open(self.img['css']['abs_output'], 'w')
        output_handler.write(css_output)
        output_handler.close()
        
    def get_max_width_image(self): # also unsetted
        max_width = 0
        max_width_index = None

        for index, img in enumerate(self.images):
            if img.setted:
                continue

            if img.width > max_width:
                max_width = img.width
                max_width_index = index

        if max_width_index is not None:
            return self.images[max_width_index]
        else:
            return None

    def get_max_height_image(self): # also unsetted
        max_height = 0
        max_height_index = None

        for index, img in enumerate(self.images):
            if img.setted:
                continue

            if img.height > max_height:
                max_height = img.height
                max_height_index = index

        if max_height_index is not None:
            return self.images[max_height_index]
        else:
            return None

class CssImage:
    def __init__(self, sprite_image):
        self.width = str(sprite_image.width) + "px"
        self.height = str(sprite_image.height) + "px"
        self.background_position = "%s %s" % (
            '0' if sprite_image.x == 0 else '-' + str(sprite_image.x) + 'px',
            '0' if sprite_image.y == 0 else '-' + str(sprite_image.y) + 'px'
        )
        self.name = sprite_image.filename.split('.')[0]

class CssCanvas:
    def __init__(self, canvas):
        self.width = str(canvas.width) + "px"
        self.height = str(canvas.height) + "px"

class SpriteProcesser:

    def __init__(self, config):
        self.config = config

    def process(self):
        imgs = self.config.imgs
        for img in imgs:
            Sprite(config, img).render()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError('Missing config file.')

    config_path = os.path.abspath(sys.argv[1])
    config = Config(config_path)

    SpriteProcesser(config).process()
