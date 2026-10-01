"""Exact benign tests. No network, user data, traffic linking, or attack policies."""
import copy,json,random,resource,sys,tempfile,time,unittest
from fractions import Fraction as F
from itertools import combinations,product
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from model import kernel
from producer import make,minimum_tree,hierarchy_witness,sparsify
from checker import check,InvalidCertificate,read
from oracle import capacity
from campaign import base

COUNTS={}

def tv(p,q):return sum(abs(x-y) for x,y in zip(p,q))/2

def cap(rows):return sum(map(max,zip(*rows)))

def all_trees(n):
    if n==2:yield [(0,1)];return
    for seq in product(range(n),repeat=n-2):
        degree=[1]*n
        for x in seq:degree[x]+=1
        edges=[]
        for x in seq:
            leaf=next(i for i,d in enumerate(degree) if d==1)
            edges.append(tuple(sorted((leaf,x))));degree[leaf]-=1;degree[x]-=1
        ends=[i for i,d in enumerate(degree) if d==1]
        edges.append(tuple(ends));yield edges

class SummaryTests(unittest.TestCase):
    def verify_summary(self,n,d,enumerate_trees=False):
        tree=minimum_tree(n,d);bound=1+sum(d[tuple(e)] for e in tree)
        rows=hierarchy_witness(n,d)
        self.assertTrue(all(sum(row)==1 for row in rows));self.assertLessEqual(len(rows[0]),2*n-1)
        self.assertEqual(cap(rows),bound)
        self.assertTrue(all(tv(rows[i],rows[j])<=d[i,j] for i,j in combinations(range(n),2)))
        if enumerate_trees:self.assertEqual(bound,1+min(sum(d[e] for e in t) for t in all_trees(n)))
    def test_exhaustive_upper_summaries(self):
        count=0
        for n,levels in ((3,[F(i,4) for i in range(5)]),(4,[F(0),F(1,2),F(1)])):
            edges=list(combinations(range(n),2))
            for vals in product(levels,repeat=len(edges)):
                self.verify_summary(n,dict(zip(edges,vals)),True);count+=1
        COUNTS['exhaustive_summary_matrices']=count
    def test_random_summaries(self):
        rng=random.Random(913207);count=0
        for n in range(2,9):
            for _ in range(20):
                d={e:F(rng.randrange(21),20) for e in combinations(range(n),2)}
                self.verify_summary(n,d,n<=6);count+=1
        COUNTS['seeded_summary_matrices']=count;COUNTS['summary_seed']=913207
    def test_random_channels(self):
        rng=random.Random(821407);count=0
        for n in range(2,9):
            for columns in range(2,10):
                for _ in range(5):
                    rows=[]
                    for s in range(n):
                        nums=[rng.randrange(1,10) for _ in range(columns)];z=sum(nums)
                        rows.append([F(v,z) for v in nums])
                    d={e:tv(rows[e[0]],rows[e[1]]) for e in combinations(range(n),2)}
                    tree=minimum_tree(n,d);self.assertLessEqual(cap(rows),1+sum(d[tuple(e)] for e in tree));count+=1
        COUNTS['seeded_finite_channels']=count;COUNTS['channel_seed']=821407
    def test_fixed_prior_boundary(self):
        rho=[F(3,10),F(1,10),F(3,5)]
        supports=[{0},{0,1},{2},{1,2},{0,1,2}];weights=list(map(F,['1/5','3/5','3/5','1/5','1/5']))
        rows=[[w if i in S else F(0) for S,w in zip(supports,weights)] for i in range(3)]
        d={(0,1):F(1,5),(1,2):F(3,5),(0,2):F(4,5)};h=hierarchy_witness(3,d)
        vulnerability=lambda P:sum(max(rho[i]*P[i][z] for i in range(3)) for z in range(len(P[0])))
        self.assertEqual(vulnerability(rows),F(21,25));self.assertEqual(vulnerability(h),F(4,5))
        self.assertEqual(cap(rows),cap(h));self.assertTrue(all(sum(r)==1 for r in rows))
        self.assertTrue(all(tv(rows[i],rows[j])<=d[i,j] for i,j in combinations(range(3),2)))

class CertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=kernel(base());cls.dense=make(cls.model);cls.chain=make(cls.model,'ordered-chain')
    def rejected(self,m,c,reason):
        with self.assertRaises(InvalidCertificate) as raised:check(m,c)
        self.assertIn(reason,str(raised.exception))
    def test_valid_and_separated_modes(self):
        a=check(self.model,self.dense);b=check(self.model,self.chain);s=check(self.model,sparsify(self.dense))
        self.assertEqual(a['capacity_bound'],b['capacity_bound']);self.assertEqual(a['bellman_obligations'],2*b['bellman_obligations'])
        self.assertFalse(s['optimality_checked']);self.assertTrue(b['optimality_checked'])
    def test_mutations(self):
        mutations=[]
        def add(name,operation,reason):mutations.append((name,operation,reason))
        add('kernel coverage',lambda m,c:m['kernel'].pop(next(iter(m['kernel']))),'kernel coverage')
        add('kernel normalization',lambda m,c:m['kernel']['0,0,0'][0].__setitem__(2,'2'),'normalized kernel')
        add('parameter semantics',lambda m,c:m['config'].__setitem__('padding','1'),'declared queue semantics')
        add('scheduler scope',lambda m,c:m['config'].__setitem__('scheduler','secret-aware'),'scheduler scope')
        add('observation boundary',lambda m,c:m['config'].__setitem__('observe_overflow',True),'kernel target')
        add('coupling coverage',lambda m,c:c['couplings'].pop(next(iter(c['couplings']))),'coupling coverage')
        add('coupling marginal',lambda m,c:c['couplings'][next(iter(c['couplings']))][0].__setitem__(4,'2'),'coupling marginals')
        add('potential coverage',lambda m,c:c['potentials'].pop(next(iter(c['potentials']))),'potential coverage')
        add('negative potential',lambda m,c:c['potentials'].__setitem__(next(iter(c['potentials'])),'-1'),'potential range')
        add('terminal mismatch',lambda m,c:c['potentials'].__setitem__('0,1,4,0,0,0','1/2'),'terminal potential')
        add('Bellman underestimate',lambda m,c:c['potentials'].__setitem__('0,1,0,1,0,0','0'),'Bellman inequality')
        add('initial underestimate',lambda m,c:c['distances'].__setitem__('0,1','0'),'initial distance bound')
        add('tree size',lambda m,c:c['tree'].pop(),'tree size')
        add('tree duplicate',lambda m,c:c['tree'].__setitem__(1,c['tree'][0]),'tree edge')
        add('capacity arithmetic',lambda m,c:c.__setitem__('capacity_bound','1'),'capacity arithmetic')
        add('rational denominator',lambda m,c:c['distances'].__setitem__('0,1','1/0'),'noncanonical rational')
        add('rational encoding type',lambda m,c:c['distances'].__setitem__('0,1',0.1),'rational encoding')
        add('unreduced rational',lambda m,c:c['distances'].__setitem__('0,1','2/4'),'noncanonical rational')
        add('decimal rational',lambda m,c:c['distances'].__setitem__('0,1','0.5'),'noncanonical rational')
        add('leading-zero rational',lambda m,c:c['distances'].__setitem__('0,1','01/2'),'noncanonical rational')
        add('whitespace rational',lambda m,c:c['distances'].__setitem__('0,1',' 1/2'),'noncanonical rational')
        add('negative-zero rational',lambda m,c:c['distances'].__setitem__('0,1','-0'),'noncanonical rational')
        add('arrival sequence type',lambda m,c:m['config'].__setitem__('arrival_rates','0'),'config sequences')
        add('initial sequence type',lambda m,c:m['config'].__setitem__('initial_queues',0),'config sequences')
        add('kernel row type',lambda m,c:m['kernel'].__setitem__('0,0,0',{}),'kernel row encoding')
        add('kernel entry shape',lambda m,c:m['kernel']['0,0,0'].__setitem__(0,['0',0]),'kernel entry encoding')
        add('coupling row type',lambda m,c:c['couplings'].__setitem__(next(iter(c['couplings'])),{}),'coupling row encoding')
        add('coupling entry shape',lambda m,c:c['couplings'][next(iter(c['couplings']))].__setitem__(0,['0',0,'0',0]),'coupling entry encoding')
        add('tree type',lambda m,c:c.__setitem__('tree',{}),'tree encoding')
        add('unknown model field',lambda m,c:m.__setitem__('ignored',True),'model schema')
        add('unknown config field',lambda m,c:m['config'].__setitem__('token_rule','real-only'),'config schema')
        add('unknown certificate field',lambda m,c:c.__setitem__('note','ignored'),'certificate schema')
        for name,operation,reason in mutations:
            with self.subTest(name=name):
                m,c=copy.deepcopy(self.model),copy.deepcopy(self.dense);operation(m,c);self.rejected(m,c,reason)
        COUNTS['basic_certificate_mutations']=len(mutations)
    def test_nonminimum_tree_is_not_dense_optimal(self):
        c=copy.deepcopy(self.dense);c['tree']=[[0,j] for j in range(1,4)]
        c['capacity_bound']=str(1+sum(F(c['distances'][f'0,{j}']) for j in range(1,4)))
        self.rejected(self.model,c,'minimum tree cycle property')
        self.assertTrue(check(self.model,sparsify(c))['valid'])
    def test_order_and_canonical_specific_mutations(self):
        # A004 and A005 are rejected only in their supplied label index.  Both
        # admit the common permutation (0,2,1); the checker intentionally does
        # not search for that relabeling.
        for case in ('A004','A005'):
            original=read(ROOT/'inputs'/f'{case}.json')
            dense=make(original)
            self.assertEqual(dense['capacity_bound'],'2')
            self.assertEqual(1+sum(F(dense['distances'][f'{i},{i+1}']) for i in range(2)),3)
            with self.assertRaises(ValueError):make(original,'ordered-chain')
            rejected=sparsify(dense);rejected['scope']='ordered-chain'
            self.rejected(original,rejected,'given-index joint parameter order')

            permutation=(0,2,1)
            config=copy.deepcopy(original['config'])
            config['arrival_rates']=[config['arrival_rates'][i] for i in permutation]
            config['initial_queues']=[config['initial_queues'][i] for i in permutation]
            relabeled=kernel(config)
            relabeled_dense=make(relabeled)
            relabeled_chain=make(relabeled,'ordered-chain')
            self.assertEqual(check(relabeled,relabeled_dense)['capacity_bound'],'2')
            self.assertEqual(check(relabeled,relabeled_chain)['capacity_bound'],'2')
        COUNTS['relabelled_order_controls']=2

        c=copy.deepcopy(self.chain);key='0,1,0,0,1';left=self.model['kernel']['0,0,1'];right=self.model['kernel']['1,0,1']
        c['couplings'][key]=[[yi,qi,yj,qj,str(F(pi)*F(pj))] for yi,qi,pi in left for yj,qj,pj in right]
        self.rejected(self.model,c,'canonical ordered coupling')
        padded=base(H=1);padded['padding']='1';m=kernel(padded);c=make(m,'ordered-chain')
        c['potentials']['0,1,0,1,0,0']='1/10';self.rejected(m,c,'canonical Bellman equality')
        c=make(m,'ordered-chain');c['distances']['0,1']='1/10';self.rejected(m,c,'canonical initial equality')
        COUNTS['ordered_specific_negative_checks']=5
    def test_duplicate_json_key(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'input.json';p.write_text('{"a":1,"a":2}')
            with self.assertRaises(InvalidCertificate):read(p)
    def test_tiny_oracle_and_certificate(self):
        exact,info=capacity(self.model)
        self.assertEqual(exact,F(761,500));self.assertEqual(F(self.dense['capacity_bound']),F(1028,625))
        self.assertGreater(info['oracle_nodes'],0)
        with self.assertRaises(RuntimeError):capacity(self.model,node_cap=1)

class BoundaryTests(unittest.TestCase):
    def test_slot_marginals_do_not_compose(self):
        rows=[[F(1,2),0,0,F(1,2)],[0,F(1,2),F(1,2),0]]
        self.assertEqual(cap(rows),2)
        for index in (0,1):
            marginals=[]
            for row in rows:
                marginals.append([sum(row[z] for z in range(4) if ((z>>(1-index))&1)==bit) for bit in (0,1)])
            self.assertEqual(tv(*marginals),0)
    def test_queue_reset_does_not_erase_history(self):
        c=base(m=2,B=1,H=1);c.update(arrival_rates=['0','0'],initial_queues=[0,1],padding='0')
        m=kernel(c);self.assertEqual(capacity(m)[0],2)
        self.assertEqual({q for s in range(2) for _,q,_ in m['kernel'][f'{s},{c["initial_queues"][s]},1']},{0})
    def test_padding_observation_boundary(self):
        c=base();c['padding']='1';self.assertEqual(capacity(kernel(c))[0],1)
        c['observe_overflow']=True;self.assertEqual(capacity(kernel(c))[0],F(224,125))
    def test_hidden_actions_are_excluded(self):
        # A tiny abstract action channel illustrates the excluded premise only.
        self.assertEqual(cap([[F(1),F(0)],[F(0),F(1)]]),2)
        m=kernel(base());m['config']['scheduler']='secret-aware'
        with self.assertRaises(InvalidCertificate):check(m,make(kernel(base())))
    def test_real_only_accounting_boundary(self):
        # Deterministic two-slot toy: full cover, b=1, no refill. Changing the
        # token rule makes an empty queue emit twice while a real job consumes
        # its only token. No such alternative semantics is admitted by checker.
        traces=[]
        for initial in (0,1):
            q,b=initial,1;emissions=[]
            for _ in range(2):
                a=int(b>0);real=int(a and q>0);emissions.append(a)
                q-=real;b-=real
            traces.append(tuple(emissions))
        self.assertEqual(traces,[(1,1),(1,0)]);self.assertEqual(cap([[1,0],[0,1]]),2)


def main():
    start=time.process_time();suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=dict(test_methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                successful=result.wasSuccessful(),cpu_seconds=time.process_time()-start,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**COUNTS)
    path=ROOT/'results'/'tests.json';path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    if not result.wasSuccessful():raise SystemExit(1)

if __name__=='__main__':main()
