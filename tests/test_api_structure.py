import pytest

from api.api import structure_details


from tests.common import data_model

@pytest.mark.usefixtures("data_model")
class TestApiStructure:
    async def test_get_structure_detail(self, data_model):
        result = await structure_details(structure_id=1, dm=data_model)
        assert result.inchi == 'InChI=1S/C2H7NO/c1-2(3)4/h2,4H,3H2,1H3/t2-/m1/s1'
        assert result.smiles == 'C[C@H](N)O'
        assert result.formula == 'C2H7NO'
        assert result.properties['fr_thiazole'] == 0.0
        assert result.properties['fr_thiocyan'] == 0.0
        assert result.properties['fr_thiophene'] == 0.0
