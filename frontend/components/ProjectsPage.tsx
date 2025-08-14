import React, { useState } from 'react';
import { 
  FolderOpen, Plus, Search, Filter, MoreVertical, Edit, Copy, Trash2, 
  Share, Download, Clock, CheckCircle, AlertCircle, XCircle, Zap, Settings,
  Calendar, User, FileText, BarChart3
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigation } from './AppShell';

interface Project {
  id: string;
  name: string;
  description: string;
  type: 'server' | 'client';
  mode: 'quick' | 'advanced';
  language: string;
  status: 'completed' | 'in_progress' | 'failed' | 'draft';
  createdAt: Date;
  updatedAt: Date;
  author: string;
  filesCount: number;
  size: string;
  tags: string[];
}

type SortOption = 'name' | 'created' | 'updated' | 'status';
type FilterOption = 'all' | 'server' | 'client' | 'quick' | 'advanced' | 'completed' | 'in_progress' | 'failed';

export const ProjectsPage: React.FC = () => {
  const { setPage, setMode } = useNavigation();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('updated');
  const [filterBy, setFilterBy] = useState<FilterOption>('all');
  const [showFilters, setShowFilters] = useState(false);

  // Mock projects data - in real app this would come from API
  const mockProjects: Project[] = [
    {
      id: '1',
      name: 'File System Server',
      description: 'Basic file operations MCP server with read/write capabilities',
      type: 'server',
      mode: 'quick',
      language: 'TypeScript',
      status: 'completed',
      createdAt: new Date('2024-01-15'),
      updatedAt: new Date('2024-01-16'),
      author: 'You',
      filesCount: 8,
      size: '2.3 MB',
      tags: ['filesystem', 'basic', 'typescript']
    },
    {
      id: '2',
      name: 'Database Integration Server',
      description: 'Production-ready database MCP server with PostgreSQL support',
      type: 'server',
      mode: 'advanced',
      language: 'Python',
      status: 'in_progress',
      createdAt: new Date('2024-01-10'),
      updatedAt: new Date('2024-01-14'),
      author: 'You',
      filesCount: 15,
      size: '5.7 MB',
      tags: ['database', 'postgresql', 'production']
    },
    {
      id: '3',
      name: 'API Client',
      description: 'REST API client for external service integration',
      type: 'client',
      mode: 'quick',
      language: 'TypeScript',
      status: 'completed',
      createdAt: new Date('2024-01-08'),
      updatedAt: new Date('2024-01-09'),
      author: 'You',
      filesCount: 5,
      size: '1.2 MB',
      tags: ['api', 'client', 'rest']
    }
  ];

  const getStatusIcon = (status: Project['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'draft':
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusText = (status: Project['status']) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'in_progress':
        return 'In Progress';
      case 'failed':
        return 'Failed';
      case 'draft':
        return 'Draft';
    }
  };

  const getModeIcon = (mode: Project['mode']) => {
    return mode === 'quick' ? <Zap className="h-4 w-4 text-yellow-500" /> : <Settings className="h-4 w-4 text-blue-500" />;
  };

  const filteredAndSortedProjects = mockProjects
    .filter(project => {
      if (filterBy === 'all') return true;
      if (filterBy === 'server' || filterBy === 'client') return project.type === filterBy;
      if (filterBy === 'quick' || filterBy === 'advanced') return project.mode === filterBy;
      return project.status === filterBy;
    })
    .filter(project => 
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'created':
          return b.createdAt.getTime() - a.createdAt.getTime();
        case 'updated':
          return b.updatedAt.getTime() - a.updatedAt.getTime();
        case 'status':
          return a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });

  const handleProjectAction = (action: string, project: Project) => {
    switch (action) {
      case 'edit':
        setMode(project.mode);
        setPage('chat');
        break;
      case 'duplicate':
        // TODO: Implement duplicate functionality
        break;
      case 'delete':
        // TODO: Implement delete functionality
        break;
      case 'share':
        // TODO: Implement share functionality
        break;
      case 'download':
        // TODO: Implement download functionality
        break;
    }
  };

  return (
    <div className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              My Projects
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Manage and organize your MCP server projects
            </p>
          </div>
          <Button
            onClick={() => setPage('chat')}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                <FolderOpen className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Projects</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{mockProjects.length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900/20 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Completed</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {mockProjects.filter(p => p.status === 'completed').length}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
                <Clock className="h-6 w-6 text-yellow-600 dark:text-
          v>
        l-4">
          
               100">
        
             
              </div>
            </div>
          </div>
          
          <div className="bg-white dark: p-6">
            <div className="flex itemcenter">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/20 rd-lg">
                <BarChart3 className=
              </div>
             
                <p className="text-sm fo
                <p className="text-2xl f">
                  {mockPh}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Search and Filter Bar */}
        <div classNameb-8">
          <div className="flex>
            <Search className="absolute left-3 top-1/2 transform -translat" />
            <input
              type="t
              placeholder="Search projects..."
              value={searchQ}
              onCe)}
         
               )}         
   /span>      <                3}
 th -t.tags.lengojec    +{pr            >
        rounded"text-xs gray-400 ark:text- dy-600t-graray-700 tex0 dark:bg-gy-10grag-2 py-1 bName="px- <span class                    
  (th > 3 &&.lenggs{project.ta                ))}
                 n>
           </spa                 ag}
           {t       >
                    
         ed" round400 text-xsgray-rk:text-ay-600 daext-grray-700 tg-gark:by-100 d-1 bg-grapyx-2 ssName="p        cla                }
ey={tag        k                    <span
                 ag) => (
 ((t0, 3).mapgs.slice({project.ta                   4">
 mb-p gap-1 wrax flex-Name="flev class <di           */}
      * Tags       {/           /div>

            <  div>
          </           
    iv>         </d             n>
}</spa.authorn>{project <spa               
        -3 w-3" />e="hr classNamse          <U    
          x-1">pace-enter sflex items-cme="classNa   <div                    iv>
    </d          >
        ng()}</spaneDateStrit.toLocal.updatedA{projectspan>  <                     />
  -3"Name="h-3 wendar class<Cal                   -1">
     nter space-xx items-cee="fleclassNam   <div                00">
    ext-gray-4:tdark-500 rayt-gxs texext- t-betweener justifyent items-c"flexame=lassN c        <div         
                 
         </div>          
       </span>ect.size} <span>{proj                  iv>
          </d            /span>
   t} files<sCounoject.file>{pr  <span                     >
  /h-3 w-3"e="t classNamleTex  <Fi               ">
       pace-x-1er scents-lex item"flassName=div c         <          ">
   00ay-4ext-grdark:tray-500 xs text-g text-tweentify-beuster jenms-cflex iteme="Naiv class  <d             
                        v>
      </di        n>
       guage}</spat.lanjecn>{pro  <spa              
         </div>              pan>
     de</sde} Mot.mojecze">{pro="capitalian className         <sp              
 }ect.mode)on(proj{getModeIc                   1">
     ace-x-sper x items-centflessName="<div cla                     00">
 ray-4:text-grk da00gray-5ext-t-xs t textify-betweenenter jus items-cflexassName="    <div cl       
         ">-y-2 mb-4aceame="spiv classN<d           }
       tadata *//* Me        {          </p>

             n}
     escriptioject.d    {pro                
p-2">line-clamb-4 -sm m-400 textayxt-grark:te0 dext-gray-60ssName="tla c     <p            on */}
 cripti* Des          {/       

 div>     </    
         div>   </               s */}
  onti acown menu for Add dropdDO:{/* TO                      utton>
</B                  />
    -4 w-4" "hssName=al clartic <MoreVe                       
m">t" size="siant="ghoson varButt    <                ve">
  ="relatiiv className    <d                
                div>
        </                </div>
                      v>
  </di                  pan>
             </s              tatus)}
   t(project.satusTexetSt {g                    
       ray-400">-grk:texty-500 da text-grae="text-xsclassNamn   <spa                      status)}
  ect.con(proj{getStatusI                         1">
 -x-2 mt-r spaceteenems-cflex itclassName="       <div                3>
     </h                 e}
    .namroject      {p                  ">
  100 truncatek:text-gray--900 dargraybold text-semifont-ame="assNcl  <h3                       iv>
    <d            iv>
      </d             >
         " /ue-400-bldark:textt-blue-600 -6 texame="h-6 wrOpen classN      <Folde           ">
       gounded-l900/20 rg-blue--100 dark:blue"p-2 bg-blassName= <div c                  >
   "r space-x-3enteex items-ce="flam <div classN               4">
    etween mb-rt justify-bex items-staflclassName="<div                 er */}
  ead       {/* H       ">
    p-6className="       <div                   >
"
     -700border-gray-200 dark:order-grayr bdow borde-shaiong transitdow-lr:shahadow hoveded-lg sroun0 bg-gray-80ark: dg-whiteName="bass     cl       t.id}
    jec   key={pro            iv
          <d(
     > t) =(projecjects.map(SortedProilteredAnd   {f         
s-3 gap-6">g:grid-col2 lls-co1 md:grid--cols-gridame="grid assN cldiv
          <: (        ) 
  </div>   iv>
       </d   n>
          </Butto  
         mplatesTe     Browse               >
          
 ')}testemplage('Pa={() => set onClick          ine"
     "outlvariant=              
     <Button         n>
  </Butto       ect
       reate Proj  C                 >
        ite"
   -700 text-whbluehover:bg-g-blue-600 ssName="b     cla           'chat')}
 => setPage(lick={()   onC                <Button
     ">
      space-x-4enter ex justify-c"flssName=v cla    <di       
         </p>}
            .'
      anced buildsation or adverck genen quihoose betweed. Ct startct to gejeP server profirst MCour  yreate   : 'C             teria.'
 filter crirch orseaing your djust 'Try a     ?           = 'all' 
 filterBy != ||chQuery    {sear      to">
    aumax-w-md mx-6 ray-400 mb-ext-g00 dark:ty-6="text-grame  <p classNa      /h3>
        <
        cts yet'}oje pr : 'Nojects found''No pro' ?  'alllterBy !== fiery ||chQu {sear            b-2">
 y-100 mraark:text-g-gray-900 dold text font-semibext-xlme="tssNa3 cla   <h
         >uto mb-4" / mx-aext-gray-400-16 w-16 tme="hNaOpen class <Folder      >
     y-16"enter pe="text-civ classNam         <d (
  ?== 0ngth =cts.leojeAndSortedPriltered{f      Grid */}
  /* Projects    {   
  )}
      </div>
          </div>
              )}
   )        
    </Button>         
      ', ' ')}lace('_{filter.rep                
          >
        apitalize"e="c   classNam            r)}
   y(filteterBFil{() => setlick=    onC       
       ="sm"        size  "}
        tline : "ou"default"er ? lt === fint={filterBy      varia         r}
     key={filte         n
       Butto    <      
      (> ilter) =map((f).lterOption[]d'] as Fifailes', 'in_progresd', '', 'completevanced'ad',  'quick, 'client',er'all', 'serv      {(['   2">
     rap gap-ex flex-wassName="fl cl     <div       ">
 mb-8dow p-4ed-lg sha0 round80ay-ark:bg-gr"bg-white d=iv className   <d
        && (ilters   {showF/}
     er Options */* Filt     {   </div>

     Button>
    </       
  </span>teriln>F  <spa     
     4" />="h-4 w-er className      <Filt  
        >-2"
      e-xacer sps-centitemame="flex  classN         ilters)}
  howFowFilters(!s> setSh={() =nClick      o
      ne" tliouriant="     va       utton 
   <B 
               /select>
      <>
     tion</opusy Statt bus">Sortat value="stion  <op       option>
   Name</rt by ">Sovalue="nameion opt   <>
         ioned</optrt by Created">Soat"cren value=    <optio
        ption>pdated</o by Uted">Sort"updaption value=          <o    >
    "
    arentorder-transp00 focus:blue-5cus:ring-bng-2 fo100 focus:riy-:text-graark dext-gray-900-gray-800 t:bgte darkg bg-whided-l00 roun-6border-gray dark:-gray-300 border py-2 bordersName="px-3 clas     
      tion)} SortOplue as.vay(e.targetsetSortB{(e) => Change=        on}
    By value={sort
            <select               
  
       </div>         />
        
sparent":border-tranue-500 focusblcus:ring-ing-2 fo100 focus:rt-gray-texy-900 dark:graay-800 text-bg-grark:g bg-white d0 rounded-lrder-gray-60ark:bo-gray-300 der borderpy-2 bord0 pr-4 -full pl-1ame="w    classN        e)}
  rget.valuery(e.tachQu setSearange={(e) =>  onCh         y}
   chQuer value={sear           ts..."
  ojecpr="Search placeholder            
  "text   type="         
  ut       <inp/>
     " t-gray-400-4 w-4 tex-y-1/2 hanslatesform -tr-1/2 trane left-3 top="absolutlassNameearch c     <S>
        relative"me="flex-1 classNa       <div
   4 mb-8">er space-x-s-centex itemassName="flv cl<di/}
         *Barnd Filter ch a Sear  {/*

         </div>div>
        </           </div>
  >
           </div
             </p>      h}
      ).lengtonth()tMew Date().ge=== nonth() atedAt.getM> p.creilter(p =ts.f{mockProjec           
       ray-100">-gdark:text900 ext-gray-ont-bold tt-2xl f"texsName=las     <p c           Month</p>
This ">ay-400rk:text-gr-gray-600 daedium textont-mext-sm fe="t classNam         <p      -4">
 mlme="div classNa     <>
           </div        " />
    urple-400xt-p dark:tet-purple-600exh-6 w-6 t"lassName= cart3arCh       <B     g">
     rounded-lple-900/20dark:bg-purpurple-100 -2 bg-me="p<div classNa            r">
  te-cen itemssName="flexv clas       <di   
  adow p-6">ded-lg sh0 roun:bg-gray-80e darkg-whitame="b <div classN     
       
       div>   </v>
         </di      
        </div>     p>
     </            
    ngth}rogress').lein_ptatus === 'er(p => p.s.filtectsoj     {mockPr            0">
 -10raydark:text-ggray-900 text-d xl font-bolxt-2="tep className          <
      s</p>>In Progresy-400"raext-g00 dark:tay-6-grdium textt-mext-sm fon="teme classNa    <p   >
         4"Name="ml-div class          <>
    iv    </d     
      />yellow-400"