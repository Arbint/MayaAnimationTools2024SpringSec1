import unreal
import os
def CreateImportTask(meshPath): 
    importTask = unreal.AssetImportTask()
    importTask.filename = meshPath
    assetName = os.path.basename(os.path.abspath(meshPath)).split(".")[0]
    importTask.destination_path = '/game/' + assetName
    importTask.automated = True # do not popup the import options
    importTask.save = True
    importTask.replace_existing = True
    return importTask

def ImportSkeletalMesh(meshPath):
    importTask = CreateImportTask(meshPath)

    importOptions = unreal.FbxImportUI()
    importOptions.import_mesh = True
    importOptions.import_as_skeletal = True
    importOptions.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)
    importOptions.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose', True)

    importTask.options = importOptions

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])
    return importTask.get_objects()[0]

def ImportAnim(mesh : unreal.SkeletalMesh, animPath):
    importTask = CreateImportTask(animPath)
    meshDir = os.path.dirname(mesh.get_path_name())
    importTask.destination_path = meshDir + "/animations"

    importOtions = unreal.FbxImportUI()
    importOtions.import_mesh = False
    importOtions.import_as_skeletal = True
    importOtions.skeleton = mesh.skeleton
    importOtions.import_animations = True

    importOtions.set_editor_property('automated_import_should_detect_type', False)
    importOtions.set_editor_property('original_import_type', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    importOtions.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)

    importTask.options = importOtions
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])
    
def ImportMeshAndAnims(meshPath, animDir):
    mesh = ImportSkeletalMesh(meshPath)
    for filename in os.listdir(animDir):
        if ".fbx" in filename:
            animPath = os.path.join(animDir, filename) 
            ImportAnim(mesh, animPath)

ImportMeshAndAnims("C:/Users/jili1/Downloads/out/Alex.fbx", "C:/Users/jili1/Downloads/out/anim")