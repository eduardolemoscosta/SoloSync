# Generated manually to handle data migration and hierarchy transition safely

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def migrate_existing_talhoes_to_propriedades(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL.split('.')[0], settings.AUTH_USER_MODEL.split('.')[1] if '.' in settings.AUTH_USER_MODEL else 'User')
    Propriedade = apps.get_model('core', 'Propriedade')
    Talhao = apps.get_model('core', 'Talhao')
    PerfilUsuario = apps.get_model('core', 'PerfilUsuario')

    # Para cada usuário que possui talhões, cria ou busca sua propriedade padrão
    for user in User.objects.all():
        talhoes_user = Talhao.objects.filter(usuario_id=user.id)
        if talhoes_user.exists():
            perfil = PerfilUsuario.objects.filter(usuario_id=user.id).first()
            nome_prop = perfil.nome_propriedade if perfil and perfil.nome_propriedade else f"Propriedade de {user.username}"
            lat = perfil.latitude_propriedade if perfil else -5.8958
            lng = perfil.longitude_propriedade if perfil else -35.7633
            
            propriedade = Propriedade.objects.create(
                usuario_id=user.id,
                nome=nome_prop,
                latitude_sede=lat,
                longitude_sede=lng,
            )
            talhoes_user.update(propriedade_id=propriedade.id)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_irrigacao_id_alter_manejo_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Propriedade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=150)),
                ('cidade', models.CharField(blank=True, max_length=100, null=True)),
                ('estado', models.CharField(blank=True, max_length=2, null=True)),
                ('latitude_sede', models.FloatField(help_text='Coordenada para centralizar o mapa da terra')),
                ('longitude_sede', models.FloatField(help_text='Coordenada para centralizar o mapa da terra')),
                ('area_total_ha', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='propriedades', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='talhao',
            name='ativo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='talhao',
            name='criado_em',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='talhao',
            old_name='coordenadas',
            new_name='coordenadas_json',
        ),
        migrations.AlterField(
            model_name='talhao',
            name='area_m2',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='talhao',
            name='tipo_solo',
            field=models.CharField(blank=True, choices=[('Arenoso', 'Arenoso'), ('Argiloso', 'Argiloso'), ('Misto', 'Misto'), ('Siltoso', 'Siltoso'), ('Outro', 'Outro')], default='Misto', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='talhao',
            name='propriedade',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='talhoes', to='core.propriedade'),
        ),
        migrations.RunPython(migrate_existing_talhoes_to_propriedades, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='talhao',
            name='propriedade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='talhoes', to='core.propriedade'),
        ),
        migrations.RemoveField(
            model_name='talhao',
            name='usuario',
        ),
    ]
