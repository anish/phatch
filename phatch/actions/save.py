# Phatch - Photo Batch Processor
# Copyright (C) 2007-2008 www.stani.be
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/
#
# Phatch recommends SPE (http://pythonide.stani.be) for editing python files.

# Embedded icon is designed by Igor Kekeljevic (http://www.admiror-ns.co.yu).

# Follows PEP8

import os
from core import ct
from core import models
from core import pil
from lib import imtools
from lib.reverse_translation import _t

#no need to lazily import these as they are always imported
import os


def init():
    global Image
    from PIL import Image
    global get_quality, get_size, InvalidWriteFormatError
    from lib.imtools import get_quality, get_size, InvalidWriteFormatError

SIZES = ['0', '10', '20', '50', '100', '200', '500', '1000', '2000', '5000']
TOLERANCES = ['0', '1', '2', '5', '10', '20', '50']


class Action(models.Action):
    """Defined variables: <filename> <type> <folder> <width> <height>"""

    label = _t('Save')
    author = 'Stani'
    email = 'spe.stani.be@gmail.com'
    version = '0.1'
    init = staticmethod(init)
    tags = [_t('default'), _t('file')]
    __doc__ = _t('Save and convert to other types')
    valid_last = True

    def interface(self, fields):
        fields[_t('File Name')] = \
            self.FileNameField(choices=self.FILENAMES)
        fields[_t('As')] = \
            self.ImageWriteTypeField(self.TYPE)
        fields[_t('In')] = \
            self.FolderField(self.DEFAULT_FOLDER, choices=self.FOLDERS)
        fields[_t('Resolution')] = self.DpiField(choices=self.DPIS)
        fields[_t('Show Type Options')] = self.BooleanField(False)
        fields[_t('PNG Optimize')] = self.BooleanField(False)
        fields[_t('JPEG Quality')] = self.SliderField(85, 1, 100)
        fields[_t('JPEG Size Maximum')] = \
            self.FileSizeField('0 kb', choices=SIZES)
        fields[_t('JPEG Size Tolerance')] = \
            self.FileSizeField('10 kb', choices=TOLERANCES)
        fields[_t('TIFF Compression')] = \
            self.TiffCompressionField(self.COMPRESSION)
        fields[_t('Metadata')] = self.BooleanField(True)

    def get_format(self, ext, photo=None):
        if ext == self.TYPE:
            if photo:
                ext = photo.info['format']
            else:
                return None
        return imtools.get_format(ext)

    def get_relevant_field_labels(self):
        """If this method is present, Phatch will only show relevant
        fields.

        :returns: list of the field labels which are relevant
        :rtype: list of strings

        .. note::

            It is very important that the list of labels has EXACTLY
            the same order as defined in the interface method.
        """
        ext = self.get_field_string('As')
        #specific file type
        relevant = ['File Name', 'As', 'In', 'Resolution']
        #<type> can be anything
        _type = ext == self.TYPE
        if _type:
            relevant.append('Show Type Options')
        advanced = _type and \
            self.get_field_string('Show Type Options') in ('yes', 'true')
        format = self.get_format(ext)
        if format == 'PNG' or advanced:
            relevant.append('PNG Optimize')
        if format == 'JPEG' or advanced:
            relevant.extend(['Metadata', 'JPEG Quality',
                'JPEG Size Maximum', 'JPEG Size Tolerance'])
        if format == 'TIFF' or advanced:
            compression = self.get_field_string('TIFF Compression')
            relevant.append('TIFF Compression')
            if compression in ('<compression>', 'none'):
                relevant.append('Metadata')
        return relevant

    def apply(self, photo, setting, cache):
        #get info
        info = photo.info
        #get file values
        folder, filename, typ = self.is_done_info(info)
        format = self.get_format(typ, photo)
        if not setting('overwrite_existing_images') \
                and os.path.exists(filename):
            return photo

        #get other values
        dpi = info['dpi'] = self.get_field('Resolution', info)
        save_metadata = self.get_field('Metadata', info)
        #filename
        filename = self.ensure_path_or_desktop(folder, photo, filename,
            desktop=setting('desktop'))
        #construct options
        options = {'dpi': (dpi, dpi)}
        if format == 'PNG':
            optimize = self.get_field('PNG Optimize', info)
            if optimize:
                options['optimize'] = 1
        elif format == 'JPEG':
            jpg_size = self.get_field('JPEG Size Maximum', info)
            quality = self.get_field('JPEG Quality', info)
            if jpg_size:
                im = photo.get_flattened_image()
                delta = self.get_field('JPEG Size Tolerance', info)
                #check necessity
                # only if file is bigger than desired size
                size = get_size(im, 'JPEG', quality=quality)
                if size > jpg_size + delta:
                    quality = get_quality(im, size=jpg_size,
                        up=quality, format='JPEG', delta=delta)
            options['quality'] = quality
        elif format == 'TIFF':
            compression = self.get_field('TIFF Compression', info)
            options['compression.tif'] = compression

        #save
        try:
            photo.save(filename, format=format,
                save_metadata=save_metadata, **options)
        except InvalidWriteFormatError:
            filename = os.path.splitext(filename)[0] + '.png'
            photo.log('%s format has been saved as PNG\n' % format)
            photo.save(filename, format='PNG',
                save_metadata=save_metadata, **options)

        return photo

    def is_done_info(self, info):
        folder = self.get_field('In', info)
        filename = self.get_field('File Name', info)
        typ = self.get_field('As', info)
        return folder, os.path.join(folder, '%s.%s' % (filename, typ)), typ

    def is_overwrite_existing_images_forced(self):
        return (self.get_field_string('In') == self.FOLDER) and\
            (self.get_field_string('File Name') == self.FILENAME) and\
            (self.get_field_string('As') == self.TYPE)

    icon = \
'x\xda\x01\xaa\x0bU\xf4\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x000\x00\
\x00\x000\x08\x06\x00\x00\x00W\x02\xf9\x87\x00\x00\x00\x04sBIT\x08\x08\x08\
\x08|\x08d\x88\x00\x00\x0baIDATh\x81\xd5\x99{l[U\x9e\xc7?\xf7^\xdb\xb1c;\xb1\
\xe3\xb8v\\\xb5I\xd3$0@h\x11\x85\x02E4B\xd0\xaaM\xba\xedj\xe8\xd0e\x1e\x1a1\
\xa3]\x8d\x06\xb1+\xad4\xd5J\xbb"\x83\x96\xfe\xb1\xaaf\xe9\xee\x82F\xc30\x9a\
\x85\x9d\x11\xa8\x12\x15iCy\xa4Q_\xd3i\x02\xcdc\x93\x16hi\xda\xe6\xfdp\x1c\'\
q\x12\xe7>\xf7\x0f\xfb\x9a\x1b\xd7I[\x9a.\x9a#\x1d\xf9\x9es,\x9f\xef\xf7\xfb\
\xfb\xfe~\xe7\xdek\xc10\x0c\xfe\x92\x9b\xf8m\x03\xb8\xdd\xf6\x17O\xc0v\'\x7f\
\xfc\xe8\xd1\xa3\xff`\xb7\xdb\xf7\xc8\xb2\xfc\xec\xf6\xed\xdb\xaf\xdd\x89=\
\x84;\x91\x03MMM\x85\xc0\xdb~\xbf\x7f\x87$I\xcc\xcc\xccLONN\xfe`\xfb\xf6\xed\
\r\xcb\xbd\xd7\xb2\x13hhhx\xc0\xef\xf7\xbf\xef\xf3\xf9V\x99s\x86a \xcb\xb2\
\x11\x8f\xc7\xff\xd3f\xb3\xfdcMM\x8d\xba\\\xfb-+\x81\x0f?\xfc\xf0\x85`0\xf8+\
\xb7\xdbm7\x0c\x03\xc30\xd0u=\xf3\xa9i\x1a\xd3\xd3\xd3m\xb3\xb3\xb3;\xb7m\
\xdb\xd6\xbf\x1c{.\x0b\x81\x83\x07\x0fz\x02\x81\xc0\xdb\xe1px\x97\xc3\xe1\
\xc8\x006\xbb\xa6i\x999UU\x99\x9f\x9f\x8f\xcf\xce\xce\xfe`\xcb\x96-\x8d\xdf:\
\x81\x0f>\xf8\xa0\xda\xe7\xf3\x1d\t\x87\xc3\xabEQ\\\x00V\xd3\xb4\xccX\xd3\
\xb4\x05s\x9a\xa6\x19sss\xbf\x9a\x98\x98\xd8\xbb{\xf7n\xed[!\xf0\xd1G\x1f\
\xfdm$\x12\xf9/\xbf\xdfo7\xc1YU\xcf5\x97MDU\xd53\xaa\xaa>\xb3u\xeb\xd6\xa1\
\xff7\x02G\x8e\x1c\xc9w\xbb\xdd\xbf/--\xdd\x9d\x97\x97\x97S\xed\xec\xb1\xaa\
\xaa\x8b\xaei\x9a6\xa6(\xca\xdf\xd4\xd6\xd6\x1e\xbb\xe3\x04\x1a\x1b\x1b\xbfS\
TT\xd4\x18\x89D\xd6\x88\xa2\x98IR+\xc0\x9bQ\xdeJ&\xfd=]\xd3\xb4_\xb6\xb5\xb5\
\xfd\xebK/\xbd\xa4\xdf\x11\x02G\x8f\x1e\xfdQ(\x14\xfaM \x10\xc8\xd3\xf5\xd4\
\x1e\xd6d\xb5&\xac\t,[y\x93p.B\x00\x82 |"\x8a\xe2\xf7\xb7m\xdb6\xb6l\x04\x8e\
\x1f?\xee\xd44\xed7\xa1P\xe8\x87N\xa73\xb3\x99\xb5L\xe6\x02\x97\x1d\x81\xec5\
s>G\x1b\x14\x04aOmm\xed\xa9\xdb&\xd0\xd0\xd0PQXXx8\x18\x0c\xde-\x8ab\x068\
\x90\x01l\xad:\xa6\x9d\x80E\xab\x90u\xbcDS\x05A\xf8\xe7\xda\xda\xda\x7f\x03\
\x16\x05\xb9$\x81\xc6\xc6\xc6g\x8b\x8a\x8a~\xe7\xf5z\xf3\xcd9\x13\xb0\x95\
\x84\xf5\xb02\xc1Y\x89\xa8\xaaz]Dn\xa15\xda\xed\xf6\x1fm\xdd\xba5v\xd3\x04\
\x0e\x1e<\xe8(,,\xfc\x0f\xbf\xdf\xffwv\xbb\x1dA\x10\x16\xd8&\x1b\xb8ulU6\x97\
\xea\xdf\xb0l\xf7\x1a\x86\xf1\xec\x8e\x1d;\xce\xde\x90\xc0\xe1\xc3\x87\xd7\
\xb8\\\xaeC\x05\x05\x05\xebDQD\x10\x84\x0c@+\x11\xab\xeaV2\xd9>\xb7F\xe2V\
\x9a\xb9/dDS\x0c\xc3\xd8\xbbc\xc7\x8e\x7f_\x94\xc0\x91#Gv\xb9\xdd\xee\xffv\
\xb9\\\x05\xd9?f\xaaj\xb5\x8fi\x85\\6\xb2*\x7f\xb3`\xad\xa0s\x91H\xf7C\xaa\
\xaa>\xbfk\xd7\xaex\x86@CC\x83W\x14\xc5W=\x1e\xcf\xf3v\xbb}\xd1M\xadI\x97\
\x0b\xb45"7\x02.\x08\xc2\x02\xe0\xd9\xe0\xad\x04,%\xd6\xc4\xd0\xe7\xf7\xfb\
\x7f\xf9\xc8#\x8f\xbc)\x02\xbc\xf3\xce;{\x82\xc1\xe0\xf3yyy\xd7\x1d:\xaa\xaa\
f\xba\xa6i(\x8a\x82,\xcb(\x8a\x82\xa2(\x995s\xbc\x94\xea&PQ\x143]\x92$L\xab\
\x9a\xd7\xd6\xf9\xec\xee\xf5zy\xf8\xe1\x87W\x9d;w\xee\xd7\x90~\xa4\xec\xea\
\xea\xd2_y\xe5\x15\x06\x06\x06\xf0x<\x0b\x00\x99\xd7\xb2,g\x80[I\xdd\x08\xb4\
\t\xdc\n\xd2\x04\'IRf\xcd\xbc\xb6\xae\x9b\xf3\xe68\x1c\x0eSQQ\xc1\xcb/\xbf\
\xcc\xa1C\x87\x0cA\x10\x04[:D.\x80\xb7\xdez\x8b\x8d\x1b7RWW\xc7\xc8\xc8\xc8u\
\xbe\xb7\xfa\xfff\x9byvX\xd5\xcf\x1eg\xe7@\xb6uDQ\xa4\xa2\xa2\x82\xd1\xd1Q^x\
\xe1\x05dY6\xb1\t\xa2 \x08\xa2$I\x95===\x18\x86AKK\x0b\x07\x0e\x1c\xc0\xe7\
\xf3a\xb7\xdb3\xd6\xb9\x19_\xe7R=\x97\x92\xe6u\xb6\xdaf7\t\x88\xa2H~~>\xd5\
\xd5\xd5455Q__\x8f,\xcbLLL0<<,\x016\x11\x10UU\x8d\xdds\xcf=|\xf5\xd5W$\x93I\
\xa2\xd1(\xfb\xf6\xed#\x91HP\\\\|K\x8a[\x81[m\x91\xcb\xcf\xd9\xdf\xcd&\\\\\\\
LYY\x19\xfb\xf6\xed\xe3\xbd\xf7\xde\x03\xa0\xb7\xb7\x17]\xd7)++S\x01\xbb\x08\
\xd8\x04Ap\'\x93I\xd6\xaf_O,\x16c||\x1c]\xd7y\xf3\xcd79u\xea\x14+W\xae\xccY%\
r\x81_*Q\xb3\xa3a\xb3\xd9r\xfa]\x92$\xd6\xacY\x83\xae\xeb\xbc\xf8\xe2\x8b\\\
\xbat\tEQ\xf8\xf2\xcb/Y\xbbv-\xc1`\x90d2i\x00y\x12\x90g\xb3\xd9\xfc^\xafw\
\x97 \x08B \x10\xc0f\xb3\xd1\xdf\xdfOAA\x01\xbd\xbd\xbd|\xfe\xf9\xe7l\xde\
\xbc9\x93\xb8K)oU|)"\xb9\xd4\x17\x04\x01\x87\xc3Aee%\xcd\xcd\xcd\x1c8p\x00UU\
\x99\x9c\x9cdpp\x90\r\x1b6077\x87\xae\xeb\xf4\xf5\xf5]\x8eF\xa3\x7f\x90\x00W\
"\x91\x88\x0e\x0f\x0fw;\x9d\xce\xa7\xddn\xb7]\x92$JKK\xf9\xe2\x8b/\xc8\xcf\
\xcf\'\x99Lr\xf2\xe4I\x1ex\xe0\x01\x02\x81\x00\xb3\xb3\xb3\x8b\x82\xb7\x02\\\
\xcc\xdf\xd9\x15\xc8\x8c\x9a\xcf\xe7#\x12\x89\xb0\x7f\xff~\x9a\x9b\x9b\x01\
\xe8\xef\xef\'//\x8f\xaa\xaa*\xa6\xa7\xa7\x99\x9f\x9f\xa7\xb3\xb3\xf3\xd4\
\x95+W\xfe\x1eHH@\x1e\xe0RUU\x1e\x1a\x1ajQ\x14e} \x10\xf0\xc9\xb2Lyy9\xfd\
\xfd\xfd(\x8aB~~>\x9d\x9d\x9d8\x1c\x0e\xee\xbb\xef>\xa6\xa7\xa7s\x82\xcf\xb6\
\x04\x90S\xf9\xec\x08D"\x11dYf\xef\xde\xbd\x0c\x0c\x0c\xa0(\n===TWWc\xb7\xdb\
\x99\x9f\x9fg||\\\xfb\xf4\xd3O\xdf\x89\xc5b\x7f\x04&\x80)\x89\xd4\xdb9;\xe0\
\x00l\xf1x\xbc;\x1a\x8dz\x8a\x8a\x8aJu]\x17\x82\xc1 \x0e\x87\x83\xc1\xc1A|>\
\x1f\x03\x03\x03\\\xbdz\x95M\x9b6\xa1(\n\xba\xae/\xaa\xbea\x18\x19\xa5sED\
\x92$\x1c\x0e\x07\xa5\xa5\xa5\x9c>}\x9a\xfd\xfb\xf7\xa3(\n\x93\x93\x93\x0c\
\x0f\x0f\xf3\xd8c\x8f111\x81\xae\xeb\\\xbe|y\xba\xb3\xb3\xf3\xd7\xb2,\xb7\
\x01\xa3\xc080-\x91:\xcc\x04K\'\x99L^\x1b\x1a\x1a\x1av\xb9\\\xf7\xb9\\.I\x92\
$\xaa\xaa\xaa\xe8\xee\xee\xa6\xb0\xb0\x10EQhkkc\xdd\xbau\x14\x14\x14 \xcbr\
\x06`v"\xe7\xca\t\xf3\xd3\xe3\xf1\x10\x0e\x87y\xf5\xd5Wy\xf7\xddw10\x18\x1d\
\x19\xc5\xe9tr\xf7\xddw3>>\x8e,\xcbttt\\\xbcr\xe5\xcao\r\xc3\xb8\n\x0c\x02#\
\xe9\x08$\xa4\xb4\x8d\r@\x07T@\x03TM\xd3\xe2CCC\xff\xabi\xdawV\xacX\xe1\x91e\
\x99{\xef\xbd\x97\xcb\x97/c\x18\x06n\xb7\x9b\x0b\x17.\xe0\xf1x\xa8\xa8\xa8`v\
v\xf6:\x80\xd9\x87\x97u-\x1c\x0e\xa3\xeb:\xbf\xf8\xa7_p\xea\xfc)>\xfb\xf3gLO\
O\xf3\xf8c\x8fc\xb3\xd9\x98\x99\x99!\x16\x8b\xe9\xad\xad\xad\x1f\xc6b\xb1\
\xf7\xd3\xc0\x07\x80! \nL\x01\xc9\\\x04\x14K\x9f\x9f\x98\x98\xe8\x8cF\xa3\
\xdeP(\xb4\xca0\x0cV\xaf^\r@__\x1f+V\xac`pp\x90\xa1\xa1!\x1e|\xf0AdY^PN\xb3\
\x0f%A\x10\xb0\xdb\xed\x94\x95\x95\xd1\xda\xdaJ}}=-\x8e\x16z\x9e\xeb\x81F\
\xd8\xfa\xe4Vf\x123h\x9aFOO\xcfL{{\xfb\xefdY\xfe,\r|\x00\x18N[g\n\x98\x03\
\x14\xc10\x0c\x84\xd4.b:\x1f\xf2\x007\xe0\x03\x02@\x08\x08;\x9d\xce\r\x8f>\
\xfa\xe8\xf7\xcb\xca\xca\xec\x0e\x87\x83@ \xc0\x89\x13\'\xa8\xae\xae&??\x1f\
\x87\xc3\xc1\xce\x9d;3\xeae\xab.\x08\x02^\xaf\x97\x92\x92\x12^\x7f\xfdu\x9a\
\x9a\x9ahs\xb5\x91x?\x01o\x80\xfb_\xdc|\xf7\xaf\xbe\xcb\xe8\xe8(]]]\x97\x07\
\x06\x06\xfe\x98\x06<\x9c\xf6|\x14\x98\x04f\x80\xf9\xb4\xd8\xba`\xb9U5s\xc0\
\x96Nh\x17P\x90&\x11\x04\xc2@\xe9\xfa\xf5\xeb\x7f\xb6a\xc3\x86b\x87\xc3\xc1\
\xca\x95+9~\xfc8\x91H\x84\x92\x92\x12\x04A\xe0\xa1\x87\x1e\xa2\xb2\xb2\x92X,\
\xb6\x80D$\x12\xc10\x0c\xea\xeb\xeb\x99\x98\x98\xe0\xc4\x9fN0U?\x05\xf3\xb0\
\xf6\x93\xb5\xec\xac\xdeIkK\xab\xde\xd1\xd1\xf1I"\x918\x91\xf6\xf9H\x1a|,\r~\
\x0e\x90\xd367\x0c\xc30\xae{"\x13\x04ALG\xc3\x0e8\x01/\xe0O\x93\x08\x01\xe1U\
\xabV\xedy\xf2\xc9\'7\xf8\xfd~\xfc~?}}}D\xa3Q\xaa\xab\xab\x11E\x91P(DMM\r\
\xb1X\x0cI\x92(//\xa7\xbd\xbd\x9d\xd7^{\r\x80\x99\x99\x19\x9a\xff\xdc\x0c\
\x05\xb0\xe5\xaf\xb7P*\x95r\xf6\xe4\xd9\xd9\x0b\x17.\xbc\xadi\xda\xc5\xb4\
\xea#\xc0\x18\x10\x07\xa6\x81d\xda\xd6\x9aa\x01\x9d\xf3\x99x\tK\x15\xa7I\x84\
\xbc^\xef\xa3O?\xfd\xf4\x9e\xb5k\xd7JN\xa7\x13\xb7\xdb\xcd\xb1c\xc7\xd8\xb8q\
#N\xa7\x13\x9b\xcd\xc6SO=EYY\x19o\xbc\xf1\x06g\xce\x9c\x01`ll\x0c\x9f\xcfGKk\
\x0b?\xfd\xc9O\xe9\xe9\xe9\xe1\xec\xd9\xb3W\x07\x06\x06\xfe\x87T\x82\x9a\xca\
\xe7\xb4\x8c\x91\x05x\xd1\xb7\x127\xb0\xd4\x8a4\x91\xb2\'\x9ex\xe2\xe7\x9b6m\
\xf2;\x1c\x0eJJJ8|\xf80\x15\x15\x15\x19\xcb\\\xbcx\x91\xb1\xb114Mchh\x88\xcd\
\x9b7322Byy9\xa7O\x9f6\xda\xdb\xdb\x9b\xa7\xa6\xa6\x8e\xa5\xadb\xfa=F*Qg\xd3\
\xaa\xab\xa6e\xae\xc3y\x13\x8f~VK\xb9\x00\x0f\x0b-Ur\xd7]w\xfd\xb0\xae\xae\
\xee~\xbf\xdfO \x10\xa0\xab\xab\x8bD"\xc1\xbau\xeb8w\xee\x1c\xc3\xc3\xc3LMMQ\
WWG[[\x1b\x86a\xd0\xdb\xdb\x9b\xec\xee\xee~[\xd3\xb4/,\xaa\x8f\x91\xaa\xefV\
\xcb\xe8\x86a,\xfa\x02\xe9\xa6\xde\xcc\xdd\x8c\xa5|>\xdf\xe3\xcf<\xf3\xcc\
\xf7*++E\x97\xcb\x85 \x08|\xfc\xf1\xc7\xcc\xcc\xcc\x90\x9f\x9fOUU\x15\x97.]B\
UU\xba\xbb\xbb\xfb\xfa\xfa\xfa\xde"e\x19\xd3\xef\xe3\xa4\xfc\xbe\xa4e\xbe\
\x11\x01\x0b\x89\x1bYjM]]\xdd\x8b555^\x87\xc3A(\x14\xa2\xbb\xbb\x9b\xabW\xaf\
\x12\x8f\xc7\x99\x9a\x9a2:::NNNN~\x9c\x06\x9dm\x19\xb3\xca,j\x99oL\xc0Bd)K\
\x85\x81\xf0\xfd\xf7\xdf\xff\xe3\xdd\xbbw\xdf\xeb\xf7\xfbiii!\x1e\x8f\xd3\
\xd7\xd77\x7f\xfe\xfc\xf9?(\x8ar\x9e\xdb\xb0\xccm\x13H\x93\xc8\xb6\x94\x07($\
e\xa9\x15@(\x18\x0c>\xf1\xdcs\xcf\xed\x1e\x1d\x1d\x15\xcf\x9c9\xd3\x7f\xed\
\xda\xb5\xdf\xf3u\x951\x0f\xa6[\xb6\xcc\xb2\x10\xb0\x90\xc8\xb6T!_G\xa3\xd8f\
\xb3\xad.,,\\?>>~\x82TI\x8c\x92R\xfd\x1b[f\xd9\x08X\x88\xe4\xb2T!\xa9$\xf7\
\xa6\xe7\x15R6\x89\xa7\x89$\xd2\xe0o\xd92\xd9\xed\xb6\xff\xa97\x0cC\x17\x04\
\xc1`\xe1\r\xe1<)k\xb8\x00\x89\xd4\xd1?\x97\x9e\x9b\xe36,\x93\xdd\x96\xed\
\x7fb\x8b\xa5$R\xaa\x9b]$E\xccz\x97\x9b\xb9\x97\xb9\xed}\x97\x8b@\xe6\x07\
\xbfNp\xb3\x0b|\x1d\x1d\x9deP\xdd\xda\xfe\x0fy\xe7\x9cX\xce.3\x93\x00\x00\
\x00\x00IEND\xaeB`\x82^\xe8\xad\\'
