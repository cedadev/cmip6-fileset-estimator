
class FilesetAppender(object):

    def __init__(self, filename, verbose=False):
        self.verbose = verbose
        self.filename = filename
        self.filesets = self.read_filesets(filename)



    def read_filesets(self, filename):
        '''

        '''
        if self.verbose:
            print("FILE :: {}".format(filename))

        filesets = set()
        with open(filename) as f:
            for line in f:
                bits = line.split()
                if len(bits) != 2:
                    continue
                 # Additional space required for granularity checker ensures that the end of the fileset is reached.
                filesets.add(bits[0]+ " ")
        return filesets

    def write_fileset(self, fileset, size):

        if self.verbose:
            print("FILESET :: {}".format(fileset))
            print("FILESET :: {}".format(self.filesets))
            print(fileset in self.filesets)

        if "{} ".format(fileset) in self.filesets:
            if self.verbose:
                print("FILESET ALREADY EXISTS")
            return

        if self.verbose:
            print("WRITING FILESET")

        with open(self.filename, "a") as f:
            f.write("{} {:.10f}\n".format(fileset, size))
        self.filesets.add(fileset)


    def get_granularity(self, filename, experiment):
        filesets = self.read_filesets(filename)
        for fileset in filesets:
            if "{}/ ".format(experiment) in fileset:
                return len(fileset.split('/'))-1

        else: return None
