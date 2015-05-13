import logging
import os
import re
import sys

from corenlp_wrapper import CoreNLPWrapper
from dep_to_4lang import DepTo4lang
from utils import ensure_dir, get_cfg, print_text_graph

__LOGLEVEL__ = 'DEBUG'
__MACHINE_LOGLEVEL__ = 'INFO'

class TextTo4lang():
    square_regex = re.compile("\[.*?\]")

    def __init__(self, cfg):
        self.cfg = cfg
        self.deps_dir = self.cfg.get('data', 'deps_dir')
        ensure_dir(self.deps_dir)
        self.corenlp_wrapper = CoreNLPWrapper(self.cfg)
        self.dep_to_4lang = DepTo4lang(self.cfg)

    @staticmethod
    def preprocess_text(text):
        t = text.strip()
        t = TextTo4lang.square_regex.sub('', t)
        t = t.replace(u"=", u"_eq_")
        t = t.replace(u"\xc2\xa0", u" ")
        t = t.replace(u"\xa0", u" ")
        t = t.strip()
        if t != text:
            logging.info(u"{0} -> {1}".format(text, t))
        return t

    def print_deps(self, parsed_sens, dep_dir=None, fn=None):
        for i, deps in enumerate(parsed_sens):
            if fn is None:
                out_fn = os.path.join(dep_dir, "{0}.dep".format(i))
            else:
                out_fn = os.path.join(dep_dir, "{0}_{1}.dep".format(fn, i))
            with open(out_fn, 'w') as f:
                f.write(
                    "\n".join(["{0}({1}, {2})".format(*dep) for dep in deps]))

    def process(self, text, dep_dir=None, fn=None):
        # logging.info("running parser...")
        preproc_text = TextTo4lang.preprocess_text(text)
        # logging.info('preproc text: {0}'.format(repr(preproc_text)))
        parsed_sens, corefs = self.corenlp_wrapper.parse_text(preproc_text)
        # logging.info("parsed {0} sentences".format(len(parsed_sens)))
        if dep_dir is not None:
            self.print_deps(parsed_sens, dep_dir, fn)

        # logging.info("loading dep_to_4lang...")
        logging.getLogger().setLevel(__MACHINE_LOGLEVEL__)

        # logging.info("processing sentences...")
        words_to_machines = self.dep_to_4lang.get_machines_from_deps_and_corefs(  # nopep8
            parsed_sens, corefs)

        # logging.info(
        #      "done, processed {0} sentences".format(len(parsed_sens)))

        return words_to_machines

def main():
    logging.basicConfig(
        level=__LOGLEVEL__,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    cfg_file = sys.argv[1] if len(sys.argv) > 1 else None
    max_sens = int(sys.argv[2]) if len(sys.argv) > 2 else None

    cfg = get_cfg(cfg_file)
    text_to_4lang = TextTo4lang(cfg)

    input_fn = cfg.get('data', 'input_sens')
    sens = [line.decode('utf-8').strip() for line in open(input_fn)]
    if max_sens is not None:
        sens = sens[:max_sens]

    words_to_machines = text_to_4lang.process(
        "\n".join(sens), dep_dir=text_to_4lang.deps_dir)
    fn = print_text_graph(words_to_machines, cfg.get('machine', 'graph_dir'))
    logging.info('wrote graph to {0}'.format(fn))

if __name__ == "__main__":
    main()
