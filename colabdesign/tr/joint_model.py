from colabdesign.af.model import mk_af_model
from colabdesign.tr.model import mk_tr_model

class mk_af_tr_model:
  def __init__(self, protocol="fixbb", use_templates=False,
               recycle_mode="last", num_recycles=0):
    assert protocol in ["fixbb","partial","hallucination","binder"]
    self.af = mk_af_model(protocol=protocol, use_templates=use_templates,
                          recycle_mode=recycle_mode, num_recycles=num_recycles)
    
    if protocol == "binder":
      def _prep_inputs(pdb_filename, chain, binder_len=50, binder_chain=None, **kwargs):
        self.af.prep_inputs(pdb_filename=pdb_filename, chain=chain,
                            binder_len=binder_len, binder_chain=binder_chain, **kwargs)
        if binder_chain is None:
          self.tr = mk_tr_model(protocol="hallucination")
          self.tr.prep_inputs(length=binder_len)
        else:
          self.tr = mk_tr_model(protocol="fixbb")
          self.tr.prep_inputs(pdb_filename=pdb_filename, chain=binder_chain)
    else:
      self.tr = mk_tr_model(protocol=protocol)

    if protocol == "fixbb":
      def _prep_inputs(pdb_filename, chain):
        self.af.prep_inputs(pdb_filename=pdb_filename, chain=chain)
        self.tr.prep_inputs(pdb_filename=pdb_filename, chain=chain)

    if protocol == "partial":
      def _prep_inputs(pdb_filename, chain, pos=None, length=None, fix_seq=False, use_sidechains=False):
        if use_sidechains: fix_seq = True
        flags = dict(pdb_filename=pdb_filename, chain=chain, pos=pos,
                     length=length, fix_seq=fix_seq)
        self.af.prep_inputs(**flags, use_sidechains=use_sidechains)
        self.tr.prep_inputs(**flags)  
      
      def _rewire(order=None, offset=0, loops=0):
        self.af.rewire(order=order, offset=offset, loops=loops)
        self.tr.rewire(order=order, offset=offset, loops=loops)
      
      self.rewire = _rewire

    if protocol == "hallucintion":
      def _prep_inputs(length=None):
        self.af.prep_inputs(length=length)
        self.tr.prep_inputs(length=length)

    self.prep_inputs = _prep_inputs

  def set_opt(self,*args,**kwargs):
    self.af.set_opt(*args,**kwargs)
    self.tr.set_opt(*args,**kwargs)

  def joint_design(self, iters=100, tr_weight=1.0, tr_seed=None, **kwargs):
    self.af.design(iters, callback=self.tr.af_callback(weight=tr_weight, seed=tr_seed), **kwargs)