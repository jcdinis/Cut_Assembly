# -*- coding: utf-8*-
import wx
import sys
import os
import vtk
from vtk.wx.wxVTKRenderWindowInteractor import wxVTKRenderWindowInteractor
from wx.lib.pubsub import setuparg1

import wx.lib.pubsub.pub as Publisher
#from wx.lib.pubsub import Publisher as pub

wildcard = "(*.stl)|*.stl"  #Leitura do formato stl 
wildcard_Ply="(*.ply)|*.ply" #escrever no formato Ply 


#-------------------------panel de corte (da esquerda)---------------------------------------------
class LeftPanel(wx.Panel):
    def __init__(self, parent, id, style):
        wx.Panel.__init__(self, parent, id, style=style)

        # usa da wx com a vtk junto (colocação do vtk dentro de wx)

        self.renderer = vtk.vtkRenderer() 
        self.Interactor = wxVTKRenderWindowInteractor(self,-1, size = self.GetSize())
        self.Interactor.GetRenderWindow().AddRenderer(self.renderer)
        self.Interactor.Render()
#-----------------------------------------------------------------------------
        #------- ajeitaro estilo da camera
        istyle = vtk.vtkInteractorStyleTrackballCamera()

        self.Interactor.SetInteractorStyle(istyle)
        #---------------------------------------------------------------

        self.VerPlano= False # inicializar o plano, para usar como plano de corte

        self.Bind(wx.EVT_IDLE, self.Restabelecer) #para funcionar o editor de corte
        


         # funcão para escrever o erro num ficheiro txt
        log_path = os.path.join('.' , 'vtkoutput.txt')
        fow = vtk.vtkFileOutputWindow()
        fow.SetFileName(log_path)
        ow = vtk.vtkOutputWindow()
        ow.SetInstance(fow)
        #--------------------------------------------------------
        #-------Criar a caixa de trabalho
        hbox=wx.BoxSizer(wx.VERTICAL)
        hbox.Add(wx.StaticText(self,-1, 'Area de Corte'))
        hbox.Add(self.Interactor,1, wx.EXPAND) # juntar com o wx, numa so janela
        

        self.SetSizer(hbox)
    #------------------------------------------------------------------
        

        self.adicionaeixos()#adiconar a função que chama o eixos
    #---------------------------------------------------------
#-----esta função faz com que o widget funciona para corte da malha do osso, caso contraio nao funciona

    def Restabelecer(self, evt):
        if self.VerPlano:
            
            self.planeWidget.On()
        
#-------------------------------------------------------------------------------------
#------------------função que constroi o eixo ----------------    

    def adicionaeixos(self):
        axes = vtk.vtkAxesActor()
        self.marker = vtk.vtkOrientationMarkerWidget()
        self.marker.SetInteractor( self.Interactor )
        self.marker.SetOrientationMarker( axes )
        self.marker.SetViewport(0.75,0,1,0.25)
        self.marker.SetEnabled(1)

#----------------------------------------------------------------------
# esta funcção faz a gravação do modelo cortado.
# esta função recebe o valor da função clipper, e depois o caminho para guardar
# usando path

    def GravarModeloCortado(self,path):
        write = vtk.vtkSTLWriter()
        write.SetInputConnection(self.clipper.GetOutputPort())
        write.SetFileTypeToBinary()
        write.SetFileName(path)
        write.Write()
        write.Update()

#-------------------------------------------------------------
        
# esta função vai ler o modelo stl:
# usando o path para encontrar o modelo a ler

    def LerSTL(self, path):
        mesh= vtk.vtkSTLReader()
        mesh.SetFileName(path)
        mesh.Update()

      # faz a mapeação dos dados do stl

        stlMapper = vtk.vtkPolyDataMapper()
        stlMapper.SetInputConnection(mesh.GetOutputPort())
        #represenatação da visualização, neste caso sem ver.

        stlActor = vtk.vtkLODActor()
        stlActor.SetMapper(stlMapper)
     
      #-------------------------------------------------------------------
        # construção do plano para corte

        plane = self.plane = vtk.vtkPlane() # chamar a função plano de corte
        PlaneCollection=vtk.vtkPlaneCollection() # cria uma colecção de planos 
        PlaneCollection.AddItem(plane) # estou a adicionar o plano de corte a essa colecção

        # faz o corte e fecha logo de imediato o polidata
        self.clipper=clipper = vtk.vtkClipClosedSurface()
        clipper.SetInputData(mesh.GetOutput())
        clipper.SetClippingPlanes(PlaneCollection) #recebe os meus planos de corte
        clipper.SetBaseColor(0.0,0.0,1.0)
        clipper.SetClipColor(0.0,0.0,1.0)
        clipper.SetScalarModeToColors()
        clipper.GenerateFacesOn() #gera a face que fecha o polidata
        

        # mapeamento da região da polidata cortada.
        clipMapper = vtk.vtkPolyDataMapper()
        clipMapper.SetInputData(clipper.GetOutput())
        clipMapper.ScalarVisibilityOn()
        #-------------------------------------------

#--------------da a cor a parte cortada----
        backProp = vtk.vtkProperty()
        backProp.SetDiffuseColor((0.0,1.0,0.0))
#---------------------------------------------------
        # faz a visualização do polidata cortada--
        clipActor = vtk.vtkActor()
        clipActor.SetMapper(clipMapper)
        clipActor.GetProperty().SetColor((0.0,1.0,0.0))
#--------------------------------------------------------

        # esta é a representação do wigdet do plano de corte

        rep = vtk.vtkImplicitPlaneRepresentation()
        rep.PlaceWidget(stlActor.GetBounds()) #é a posição dos limite aonde o plano de corte fica
        rep.SetPlaceFactor(1.25)# expandir os limite do widget para 25% 
        rep.UseBoundsOn()# mostra a fronteira
        rep.NormalToZAxisOn()#da a posição de corte, no sentido de z
        rep.OutlineTranslationOff()# nao posso mexer o widget, so posso mexer o plano de corte
        rep.PlaceWidget(mesh.GetOutput().GetBounds())#mostra aonde vai ser posicionado o widget
        
        rep.OutsideBoundsOn()
        rep.VisibilityOn()
        #............
        

# chama o proprio widget , para interação para fazer o corte
        self.planeWidget = vtk.vtkImplicitPlaneWidget2()
        self.planeWidget.SetInteractor(self.Interactor)
        self.planeWidget.SetRepresentation(rep)# adiconar a representação
        self.planeWidget.SetEnabled(0)
        self.planeWidget.AddObserver("EndInteractionEvent", self.myCallback)# vai tratar o evento para fazero corte

        self.planeWidget.On()

#---------------------------------------

# adiconar os actores ao renderer para visualização
        self.renderer.AddActor(stlActor)
        self.renderer.AddActor(clipActor)
#-------------------------------------------
#posicionar a camera para poder visualizar a volume todo        

        self.renderer.ResetCamera()
#----------------------------------------
        #faze a renderização total
        self.Interactor.Render()
        #-----------------------------

        # liga o plano para fazer funcionar o widget-
        self.VerPlano= True
#---------------------------------------------
        
#função que controla o plano de corte
    def myCallback(self, obj, event):
        obj.GetRepresentation().GetPlane(self.plane)
 #--------------------------------------------------------------       

#--------------------Panel do lado direito-------------------

class PanelRight(wx.Panel):
    def __init__(self, parent, id, style):
        wx.Panel.__init__(self, parent, id,style=style)
#faz a divisão do panel em 4 visualizações diferentes
        self.visaofrontal=VisaoFrontal(self, id=-1, style=wx.BORDER_SUNKEN)
        self.visaolateral=VisaoLateral(self, id=-1, style=wx.BORDER_SUNKEN)
        self.visaotop=VisaoTop(self, id=-1, style=wx.BORDER_SUNKEN)
        self.visaoControl=VisaoCont(self, id=-1, style=wx.BORDER_SUNKEN)
#----------------------------------------------------
        #Faz o agrupamento em caixa --------
        vbox=wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.visaolateral, 1, wx.EXPAND)
        vbox.Add(self.visaotop, 1, wx.EXPAND)


        vbox1=wx.BoxSizer(wx.VERTICAL)
        vbox1.Add(self.visaofrontal, 1, wx.EXPAND)
        vbox1.Add(self.visaoControl, 1, wx.EXPAND)
        

        hbox=wx.BoxSizer()
        hbox.Add(vbox1, 1, wx.EXPAND)
        hbox.Add(vbox, 1, wx.EXPAND)
        
        self.SetSizer(hbox)
  #-----------------------------------------------      
        
      

# contrução da class para visualização fontral
class VisaoFrontal(wx.Panel):
    def __init__(self, parent, id,style):
        wx.Panel.__init__(self, parent, id, style=style)
# tratar o render da parte fontral
        self.renderer = vtk.vtkRenderer()
        self.Interactor = wxVTKRenderWindowInteractor(self,-1, size = self.GetSize())
        self.Interactor.GetRenderWindow().AddRenderer(self.renderer)
        self.Interactor.Render()
#---------------------------------
        # a variavel que guarda o actor que foi selecionada para se mover
        self.SelectActor=None
#--------------------------------------------------
        # estilo do posicionamente da camera-----
        istyle = vtk.vtkInteractorStyleTrackballCamera()

        self.Interactor.SetInteractorStyle(istyle)
#--------------------------------------------------
        # criar o box  de trabalho-----
        hbox=wx.BoxSizer(wx.VERTICAL)
        hbox.Add(wx.StaticText(self,-1, u'Visão Frontal'))
        
        
        hbox.Add(self.Interactor,1, wx.EXPAND)
        self.SetSizer(hbox)
#-------------------------------------------
        #-------a dicionar o eixo------
        self.adicionaeixos()
        #----------------------------------------
        #Tratar os eventos neste panel
        #Clicar, Mover o rato, soltar o botão do rato
        self.Picker=vtk.vtkPropPicker()
        istyle.AddObserver("LeftButtonPressEvent",self.Clik)
        istyle.AddObserver("MouseMoveEvent", self.OnMotion)
        istyle.AddObserver("LeftButtonReleaseEvent", self.Release)
#-------------------------------------------------------------
        #cria um evente de renderizar automaiticamento nos 4 paneis

        Publisher.subscribe(self.Renderizacao, 'Renderizar')
        #----------------------------------------------------

    # faz a renderização do proprio panel    

    def Renderizacao(self, evt):
        self.Interactor.Render()
#----------------------------------


    def Clik(self, obj, event):
        iren =self.Interactor
        ren = self.renderer
        x, y = iren.GetEventPosition()# apanha as coordenadas x e y aonde foi clicado na janela
        actualY =  y
        self.Picker.Pick(x, actualY, 0, ren)
        actor=self.Picker.GetActor()

        if actor is not None:
            polidata=actor.GetMapper().GetInput()# atraves do actor conseguimos aceder ao polidata
            
            cx, cy, cz = polidata.GetCenter()#obter o centro do polidata
            self.renderer.SetWorldPoint(cx, cy, cz, 0)
            self.renderer.WorldToDisplay()
            dx, dy, dz = self.renderer.GetDisplayPoint() # dz é a profundidade do objeto com relação à camera

            self.renderer.SetDisplayPoint(x, y, dz)
            self.renderer.DisplayToWorld()
            w = self.renderer.GetWorldPoint()
            self.LastPosition= w

        self.SelectActor=actor
        
    

    def OnMotion(self, obj, event):
        if self.SelectActor is not None:
            polidata=self.SelectActor.GetMapper().GetInput()
            
            x, y = self.Interactor.GetEventPosition()
            Lx,Ly= self.LastPosition[0], self.LastPosition[2]

            cx, cy, cz = polidata.GetCenter()
            self.renderer.SetWorldPoint(cx, cy, cz, 0)
            self.renderer.WorldToDisplay()
            dx, dy, dz = self.renderer.GetDisplayPoint()

            self.renderer.SetDisplayPoint(x, y, dz)
            self.renderer.DisplayToWorld()
            w = self.renderer.GetWorldPoint()
            
            
            transform = vtk.vtkTransform()
            transform.Translate(w[0]-Lx,0,w[2]-Ly)
            transformFilter=vtk.vtkTransformPolyDataFilter()
            transformFilter.SetTransform(transform)
            transformFilter.SetInputData(polidata)
            transformFilter.Update()
            self.SelectActor.GetMapper().SetInputData(transformFilter.GetOutput())

            self.LastPosition=w
            self.SelectActor.Modified()
            Publisher.sendMessage('Renderizar')
            

    def Release(self, obj, event):
        self.SelectActor= None
        
            
        #ate aqui

    def AdicionaAtor(self, actor):
        self.renderer.AddActor(actor)
        self.posicaocamera(actor)
        self.Interactor.Render()


    def posicaocamera(self,actor):
        cam=self.renderer.GetActiveCamera()
        cam.SetPosition(0.0,-1.0,0.0)
        cam.SetFocalPoint(0.0,0.0,0.0)
        cam.SetViewUp(0.0, 0.0, 1.0)
        self.renderer.ResetCamera()


    def adicionaeixos(self):
        axes = vtk.vtkAxesActor()
        self.marker = vtk.vtkOrientationMarkerWidget()
        self.marker.SetInteractor( self.Interactor )
        self.marker.SetOrientationMarker( axes )
        self.marker.SetViewport(0.75,0,1,0.25)
        self.marker.SetEnabled(1)

        
        
class VisaoCont(wx.Panel):
    def __init__(self, parent, id,style):
        wx.Panel.__init__(self, parent, id, style=style)

        self.renderer = vtk.vtkRenderer()
        self.Interactor = wxVTKRenderWindowInteractor(self,-1, size = self.GetSize())
        self.Interactor.GetRenderWindow().AddRenderer(self.renderer)
        self.Interactor.Render()


        istyle = vtk.vtkInteractorStyleTrackballCamera()

        self.Interactor.SetInteractorStyle(istyle)

        hbox=wx.BoxSizer(wx.VERTICAL)
        hbox.Add(wx.StaticText(self,-1, u'Visualização'))
        
        
        hbox.Add(self.Interactor,1, wx.EXPAND)
        self.SetSizer(hbox)

        Publisher.subscribe(self.Renderizacao, 'Renderizar')

        self.adicionaeixos()


    def Renderizacao(self, evt):
        
        self.Interactor.Render()



    def AdicionaAtor(self, actor):
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        
        self.Interactor.Render()

    def adicionaeixos(self):
        axes = vtk.vtkAxesActor()
        self.marker = vtk.vtkOrientationMarkerWidget()
        self.marker.SetInteractor( self.Interactor )
        self.marker.SetOrientationMarker( axes )
        self.marker.SetViewport(0.75,0,1,0.25)
        self.marker.SetEnabled(1)


        


class VisaoLateral(wx.Panel):
    def __init__(self, parent, id, style):
        wx.Panel.__init__(self, parent, id, style=style)

        self.renderer = vtk.vtkRenderer()
        self.Interactor = wxVTKRenderWindowInteractor(self,-1, size = self.GetSize())
        self.Interactor.GetRenderWindow().AddRenderer(self.renderer)
        self.Interactor.Render()
        
        self.SelectActor= None
        istyle = vtk.vtkInteractorStyleTrackballCamera()

        self.Interactor.SetInteractorStyle(istyle)

        hbox=wx.BoxSizer(wx.VERTICAL)
        hbox.Add(wx.StaticText(self,-1, u'Visão Lateral'))
        hbox.Add(self.Interactor,1, wx.EXPAND)
        self.SetSizer(hbox)

        self.adicionaeixos()
        #daqui
        self.Picker=vtk.vtkPropPicker()
        istyle.AddObserver("LeftButtonPressEvent",self.Clik)
        istyle.AddObserver("MouseMoveEvent", self.OnMotion)
        istyle.AddObserver("LeftButtonReleaseEvent", self.Release)

        Publisher.subscribe(self.Renderizacao, 'Renderizar')


    def Renderizacao(self, evt):
        self.Interactor.Render()



    def Clik(self, obj, event):
        iren =self.Interactor
        ren = self.renderer
        x, y = iren.GetEventPosition()
        actualY =  y
        self.Picker.Pick(x, actualY, 0, ren)
        actor=self.Picker.GetActor()
        if actor is not None:
            polidata=actor.GetMapper().GetInput()
            
            cx, cy, cz = polidata.GetCenter()
            self.renderer.SetWorldPoint(cx, cy, cz, 0)
            self.renderer.WorldToDisplay()
            dx, dy, dz = self.renderer.GetDisplayPoint() # dz é a profundidade do objeto com relação à camera

            self.renderer.SetDisplayPoint(x, y, dz)
            self.renderer.DisplayToWorld()
            w = self.renderer.GetWorldPoint()
            self.LastPosition= w
        

        self.SelectActor=actor
        


    def OnMotion(self, obj, event):
        if self.SelectActor is not None:
            polidata=self.SelectActor.GetMapper().GetInput()
            x, y = self.Interactor.GetEventPosition()
            Lx,Ly=self.LastPosition[1], self.LastPosition[2]


            cx, cy, cz = polidata.GetCenter()
            self.renderer.SetWorldPoint(cx, cy, cz, 0)
            self.renderer.WorldToDisplay()
            dx, dy, dz = self.renderer.GetDisplayPoint()

            self.renderer.SetDisplayPoint(x, y, dz)
            self.renderer.DisplayToWorld()
            w = self.renderer.GetWorldPoint()
            
            
            transform = vtk.vtkTransform()
            transform.Translate(0,w[1]-Lx,w[2]-Ly)
            transformFilter=vtk.vtkTransformPolyDataFilter()
            transformFilter.SetTransform(transform)
            transformFilter.SetInputData(polidata)
            transformFilter.Update()
            self.SelectActor.GetMapper().SetInputData(transformFilter.GetOutput())
            
            self.LastPosition=w
            self.SelectActor.Modified()

            Publisher.sendMessage('Renderizar')

   
    def Release(self, obj, event):
        self.SelectActor= None
        
            
        #ate aqui
        
        
    def AdicionaAtor(self, actor):
        self.renderer.AddActor(actor)
        #self.renderer.ResetCamera()
        self.posicaocamera(actor)
        self.Interactor.Render()


    def posicaocamera(self,actor):
        cam=self.renderer.GetActiveCamera()
        cam.SetPosition(1.0,0.0,0.0)
        cam.SetFocalPoint(0.0,0.0,0.0)
        cam.SetViewUp(0.0, 0.0, 1.0)
        self.renderer.ResetCamera()


    def adicionaeixos(self):
        axes = vtk.vtkAxesActor()
        self.marker = vtk.vtkOrientationMarkerWidget()
        self.marker.SetInteractor( self.Interactor )
        self.marker.SetOrientationMarker( axes )
        self.marker.SetViewport(0.75,0,1,0.25)
        self.marker.SetEnabled(1)



class VisaoTop(wx.Panel):
    def __init__(self, parent, id, style):
        wx.Panel.__init__(self, parent, id, style=style)

        self.renderer = vtk.vtkRenderer()
        self.Interactor = wxVTKRenderWindowInteractor(self,-1, size = self.GetSize())
        self.Interactor.GetRenderWindow().AddRenderer(self.renderer)
        self.Interactor.Render()

        self.SelectActor= None

        istyle = vtk.vtkInteractorStyleTrackballCamera()

        self.Interactor.SetInteractorStyle(istyle)

        hbox=wx.BoxSizer(wx.VERTICAL)
        hbox.Add(wx.StaticText(self,-1, u'Visão Top'))
        hbox.Add(self.Interactor,1, wx.EXPAND)
        self.SetSizer(hbox)

        self.adicionaeixos()

        #daqui
        self.Picker=vtk.vtkPropPicker()
        istyle.AddObserver("LeftButtonPressEvent",self.Clik)
        istyle.AddObserver("MouseMoveEvent", self.OnMotion)
        istyle.AddObserver("LeftButtonReleaseEvent", self.Release)

        Publisher.subscribe(self.Renderizacao, 'Renderizar')


    def Renderizacao(self, evt):
        
        self.Interactor.Render()



    def Clik(self, obj, event):
        iren =self.Interactor
        ren = self.renderer
        x, y = iren.GetEventPosition()
        actualY =  y
        self.Picker.Pick(x, actualY, 0, ren)
        actor=self.Picker.GetActor()

        if actor is not None:
            polidata=actor.GetMapper().GetInput()
            
            cx, cy, cz = polidata.GetCenter()
            self.renderer.SetWorldPoint(cx, cy, cz, 0)
            self.renderer.WorldToDisplay()
            dx, dy, dz = self.renderer.GetDisplayPoint() # dz é a profundidade do objeto com relação à camera

            self.renderer.SetDisplayPoint(x, y, dz)
            self.renderer.DisplayToWorld()
            w = self.renderer.GetWorldPoint()
            self.LastPosition= w
            

        self.SelectActor=actor

    def OnMotion(self, obj, event):
        if self.SelectActor is not None:
            
            polidata=self.SelectActor.GetMapper().GetInput()

            x, y = self.Interactor.GetEventPosition()
            Lx,Ly= self.LastPosition[0], self.LastPosition[1]

            cx, cy, cz = polidata.GetCenter()
            self.renderer.SetWorldPoint(cx, cy, cz, 0)
            self.renderer.WorldToDisplay()
            dx, dy, dz = self.renderer.GetDisplayPoint()

            self.renderer.SetDisplayPoint(x, y, dz)
            self.renderer.DisplayToWorld()
            w = self.renderer.GetWorldPoint()

            
            transform = vtk.vtkTransform()
            transform.Translate(w[0]-Lx,w[1]-Ly,0)
            transformFilter=vtk.vtkTransformPolyDataFilter()
            transformFilter.SetTransform(transform)
            transformFilter.SetInputData(polidata)
            transformFilter.Update()
            self.SelectActor.GetMapper().SetInputData(transformFilter.GetOutput())

            self.LastPosition=w

            self.SelectActor.Modified()



            Publisher.sendMessage('Renderizar')
            
     
    def Release(self, obj, event):
        self.SelectActor= None
        
            
        #ate aqui
        

    def AdicionaAtor(self, actor):
        self.renderer.AddActor(actor)
        self.posicaocamera(actor)
        self.Interactor.Render()

    def posicaocamera(self,actor):
        cam=self.renderer.GetActiveCamera()
        cam.SetPosition(0.0,0.0,1.0)
        cam.SetFocalPoint(0.0,0.0,0.0)
        cam.SetViewUp(0.0, 1.0, 0.0)
        self.renderer.ResetCamera()



    def adicionaeixos(self):
        axes = vtk.vtkAxesActor()
        self.marker = vtk.vtkOrientationMarkerWidget()
        self.marker.SetInteractor( self.Interactor )
        self.marker.SetOrientationMarker( axes )
        self.marker.SetViewport(0.75,0,1,0.25)
        self.marker.SetEnabled(1)

#janela Principal, aonde comada todas as operações dos menus
class JanelaPrincipal(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(1300, 700))

        #Criar listas de ajudas na renderização
        self.ListaActores=[]
        self.ListaOssos=[]
        self.ListaProteses=[]
        #----------------------------------

        panel = wx.Panel(self, -1)

        self.currentDirectory = os.getcwd()

        self.LeftPanel =LeftPanel(self, id=-1, style=wx.BORDER_SUNKEN)
        self.RightPanel =PanelRight(self, id=-1, style=wx.BORDER_SUNKEN)

        hbox=wx.BoxSizer()
        hbox.Add(self.LeftPanel, 1, wx.EXPAND)
        hbox.Add(self.RightPanel, 1, wx.EXPAND)

        
        self.SetSizer(hbox)


        #criar menu para file
        MenuBar=wx.MenuBar()
        menu=wx.Menu()

       
        AbrirModelo=menu.Append(-1, "&Abrir Modelo STL")
        guardar=menu.Append(-1, "&Guardar Modelo Cortado")
        sair=menu.Append(-1, "&Sair")
        MenuBar.Append(menu, "Ficheiro")


        #--------------------------------------

        menu=wx.Menu()
        verModelo=menu.Append(-1, "&Importar Modelo Cortado")
        ImportProtese=menu.Append(-1, "&Importar Protese")
        
        MenuBar.Append(menu, "Processamento")

        #------------------------------------------------------
        # controll
        menuControl=wx.Menu()
        #sub menu
        imp = wx.Menu()
        impO = wx.Menu()
        impP = wx.Menu()
        
        trianguloDadosProteses=imp.Append(-1, 'Triangulos (STL)')
        dadosVertexProteses=imp.Append(-1, 'Vertex (Pontos)')
        self.simp =menuControl.AppendMenu(-1, "&Dados do Protese", imp)
        self.simp.Enable(False)

        #exportarProtese=menuControl.Append(-1,"&Dados do Protese")
        trianguloDadosOsso=impO.Append(-1, 'Triangulos (STL)')
        dadosVertexOsso=impO.Append(-1, 'Vertex (Pontos)')
        self.simpo = menuControl.AppendMenu(-1,"&Dados do Osso", impO)
        self.simpo.Enable(False)

        AssemblytrianguloDados=impP.Append(-1, 'Triangulos (STL)')
        AssemblydadosVertex=impP.Append(-1, 'Vertex (Pontos)')
        self.simpP=menuControl.AppendMenu(-1,"&Dados do Assemblo", impP)
        self.simpP.Enable(False)

        MenuBar.Append(menuControl, '&Exportar Dados')
        self.SetMenuBar(MenuBar)
#-----------------------------------------------------------------
    # acrescentar os eventos do menu ficheiro    
        self.Bind(wx.EVT_MENU, self.SairPrograma, sair)
        self.Bind(wx.EVT_MENU, self.AbrirSTL1, AbrirModelo)
        self.Bind(wx.EVT_MENU, self.guardarCorte, guardar)
#---------------------------------------------------------------
     # acrescentar os eventos do menu processamento-----
        self.Bind(wx.EVT_MENU, self.AbrirSTL_Cortado, verModelo)
        self.Bind(wx.EVT_MENU, self.AbrirSTL_Protese, ImportProtese)
#----------------------------------------------------------------
#------------------------acrescentar os eventos do menu exportar dados ------------------
#-----dados do assemblo----------------------------------
        self.Bind(wx.EVT_MENU, self.ExportAssemblyTri, AssemblytrianguloDados)
        self.Bind(wx.EVT_MENU, self.ExportAssemblyVertex, AssemblydadosVertex)
    #---------------------------------------------------------------------
        # da protese-----------------------------------------

        self.Bind(wx.EVT_MENU, self.ExportTriProtese, trianguloDadosProteses)
        self.Bind(wx.EVT_MENU, self.ExportVertexProtese, dadosVertexProteses)
#------------------------------------------------------------------------
        # do osso-----------------------------------------------------
        self.Bind(wx.EVT_MENU, self.ExportTriOsso, trianguloDadosOsso)
        self.Bind(wx.EVT_MENU, self.ExportVertexOsso, dadosVertexOsso)
#-----------------------------------------------------------------------       

        self.Show()
#-----------------------------------------------------------------------

 # construção das funções  principais -----------------------
 #-------------------- sair do progrma----------------------------
    def SairPrograma(self,event):
         dial=wx.MessageDialog(None, 'Pretende sair do Programa ?',u'Questão', wx.YES_NO |wx.NO_DEFAULT | wx.ICON_QUESTION)
         ret=dial.ShowModal()
         if ret==wx.ID_YES:
             self.Destroy()
#--------------------------------------------------------------

# ler o polidata e colocar no panel do lado esquerdo.

    def AbrirSTL1(self, event):
        dlg_abrir=wx.FileDialog(self, message="Escolhe o ficheiro",
                                defaultDir=self.currentDirectory,
                                defaultFile="",
                                wildcard=wildcard,
                                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                )
        if dlg_abrir.ShowModal()==wx.ID_OK:
            paths=dlg_abrir.GetPaths()
            self.LeftPanel.LerSTL(paths[0])

        dlg_abrir.Destroy()




    def AbrirSTL_Cortado(self, event):
        dlg_abrir=wx.FileDialog(self, message="Escolhe o ficheiro",
                                defaultDir=self.currentDirectory,
                                defaultFile="",
                                wildcard=wildcard,
                                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                )
        if dlg_abrir.ShowModal()==wx.ID_OK:
            paths=dlg_abrir.GetPaths()
            self.LerSTLCortado(paths[0])

        dlg_abrir.Destroy()


    def AbrirSTL_Protese(self, event):
        dlg_abrir=wx.FileDialog(self, message="Escolhe o ficheiro",
                                defaultDir=self.currentDirectory,
                                defaultFile="",
                                wildcard=wildcard,
                                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR
                                )
        if dlg_abrir.ShowModal()==wx.ID_OK:
            paths=dlg_abrir.GetPaths()
            self.LerSTLProtese(paths[0])

        dlg_abrir.Destroy()


    def guardarCorte(self, evt):
        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile="", wildcard=wildcard, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.LeftPanel.GravarModeloCortado(path)
        dlg.Destroy()


# exportar assemblagem--------------------------------------------------

    def ExportAssemblyTri(self, evt):
        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile="", wildcard=wildcard, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.salva_assembly_tri(path)
        dlg.Destroy()

    def ExportAssemblyVertex(self, evt):
        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile="", wildcard=wildcard_Ply, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.salva_assembly_vertix(path)
        dlg.Destroy()

    def salva_assembly_tri(self, path):
        assembly = self.assemblagem(self.ListaActores)
        write = vtk.vtkSTLWriter()
        write.SetInputConnection(assembly.GetOutputPort())
        write.SetFileTypeToBinary()
        write.SetFileName(path)
        write.Write()
        write.Update()


    def salva_assembly_vertix(self, path):
        assembly = self.assemblagem(self.ListaActores)
        polidata=vtk.vtkPolyData()
        polidata.SetPoints(assembly.GetOutput().GetPoints())

        write = vtk.vtkPLYWriter()
        write.SetInputData(polidata)
        write.SetFileTypeToBinary()
        write.SetFileName(path)
        write.Write()
        write.Update()

#------------------------------------------------------------------------------
# exportar a Protese------------------------------------------------------------

    def ExportTriProtese(self, evt):
        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile="", wildcard=wildcard, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.salva_triProtese(path)
        dlg.Destroy()

    def ExportVertexProtese(self, evt):
        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile="", wildcard=wildcard_Ply, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.salva_vertixProtese(path)
        dlg.Destroy()

    def salva_triProtese(self, path):
        assembly = self.assemblagem(self.ListaProteses)
        write = vtk.vtkSTLWriter()
        write.SetInputConnection(assembly.GetOutputPort())
        write.SetFileTypeToBinary()
        write.SetFileName(path)
        write.Write()
        write.Update()



    def salva_vertixProtese(self, path):
        assembly = self.assemblagem(self.ListaProteses)
        polidata=vtk.vtkPolyData()
        polidata.SetPoints(assembly.GetOutput().GetPoints())

        write = vtk.vtkPLYWriter()
        write.SetInputData(polidata)
        write.SetFileTypeToBinary()
        write.SetFileName(path)
        write.Write()
        write.Update()

#-------------------------------------------------------------------------
# exportar o osso-------------------------------------------------


        
    def ExportTriOsso(self, evt):
        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile="", wildcard=wildcard, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.salva_triOsso(path)
        dlg.Destroy()

    def ExportVertexOsso(self, evt):
        dlg = wx.FileDialog(
            self, message="Save file as ...", 
            defaultDir=self.currentDirectory, 
            defaultFile="", wildcard=wildcard_Ply, style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.salva_vertixOsso(path)
        dlg.Destroy()


    def salva_triOsso(self, path):
        assembly = self.assemblagem(self.ListaOssos)
        write = vtk.vtkSTLWriter()
        write.SetInputConnection(assembly.GetOutputPort())
        write.SetFileTypeToBinary()
        write.SetFileName(path)
        write.Write()
        write.Update()



    def salva_vertixOsso(self, path):
        assembly = self.assemblagem(self.ListaOssos)
        polidata=vtk.vtkPolyData()
        polidata.SetPoints(assembly.GetOutput().GetPoints())

        write = vtk.vtkPLYWriter()
        write.SetInputData(polidata)
        write.SetFileTypeToBinary()
        write.SetFileName(path)
        write.Write()
        write.Update()

#----------------------------------------------------------
        
    def LerSTLCortado(self, path):
        mesh= vtk.vtkSTLReader()
        mesh.SetFileName(path)
        mesh.Update()


        stlMapper = vtk.vtkPolyDataMapper()
        stlMapper.SetInputConnection(mesh.GetOutputPort())

        stlActor = vtk.vtkLODActor()
        prop=stlActor.GetProperty()
        prop.SetColor(0,0,1)
        stlActor.SetMapper(stlMapper)

        self.simpo.Enable(True)
        if self.simp.IsEnabled():
            self.simpP.Enable(True)
        
        self.RightPanel.visaofrontal.AdicionaAtor(stlActor)
        self.RightPanel.visaolateral.AdicionaAtor(stlActor)
        self.RightPanel.visaotop.AdicionaAtor(stlActor)
        self.RightPanel.visaoControl.AdicionaAtor(stlActor)
        self.ListaActores.append(stlActor)
        self.ListaOssos.append(stlActor)
        



    def LerSTLProtese(self, path):
        mesh= vtk.vtkSTLReader()
        mesh.SetFileName(path)
        mesh.Update()

      

        stlMapper = vtk.vtkPolyDataMapper()
        stlMapper.SetInputConnection(mesh.GetOutputPort())

        stlActor = vtk.vtkLODActor()
        stlActor.SetMapper(stlMapper)

        self.simp.Enable(True)
        if self.simpo.IsEnabled():
            self.simpP.Enable(True)

        self.RightPanel.visaofrontal.AdicionaAtor(stlActor)
        self.RightPanel.visaolateral.AdicionaAtor(stlActor)
        self.RightPanel.visaotop.AdicionaAtor(stlActor)
        self.RightPanel.visaoControl.AdicionaAtor(stlActor)
        self.ListaActores.append(stlActor)
        self.ListaProteses.append(stlActor)

   

    def assemblagem(self, ListaActores):
        append = vtk.vtkAppendPolyData()
        for actor in ListaActores:
            append.AddInput(actor.GetMapper().GetInput())
    
        append.Update()

        cleanFilter = vtk.vtkCleanPolyData() 
        cleanFilter.SetInputConnection(append.GetOutputPort()) 
        cleanFilter.Update()

        return cleanFilter
        









if __name__ == '__main__':
    app = wx.App(0)
    JanelaPrincipal(None, -1, 'Area de trabalho')
    app.MainLoop()
